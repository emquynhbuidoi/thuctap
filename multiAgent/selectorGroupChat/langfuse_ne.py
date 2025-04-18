from langfuse.decorators import langfuse_context
from langfuse import Langfuse
import os
import uuid
from datetime import datetime
from langfuse.media import LangfuseMedia
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    Faithfulness,
    ResponseRelevancy,
    LLMContextPrecisionWithoutReference
)
from ragas.run_config import RunConfig
from ragas.metrics.base import MetricWithLLM, MetricWithEmbeddings
from ragas.dataset_schema import SingleTurnSample
import re 

class LangfuseHandler:
    def __init__(self):
        print("[LOG]: LANGFUSE")
        os.environ["LANGFUSE_PUBLIC_KEY"] = ""
        os.environ["LANGFUSE_SECRET_KEY"] = ""

        self.langfuse = Langfuse(
            secret_key="",
            public_key="",
            host="https://cloud.langfuse.com"
        )
        self.is_newSession = True
        self.newSession_id = None                                         # Lưu session id tạo mới. Nếu đang chat với phiên mới                          
        self.tmp_file_path = None

        self.metrics = [
            Faithfulness(),
            # ResponseRelevancy(),
            LLMContextPrecisionWithoutReference(),
        ]
        key = ''            #sq2k3
        llm = ChatOpenAI(api_key=key, model='gpt-4o-mini')
        emb = OpenAIEmbeddings(api_key=key, model='text-embedding-ada-002')
        # text-embedding-3-small
        # text-embedding-3-large
        self.init_ragas_metrics(
            llm=LangchainLLMWrapper(llm),
            embedding=LangchainEmbeddingsWrapper(emb),
        )
        self.trace_id = None
        self.chats_memory_short_term = []
    
    def get_chats_memory_longterm(self, session_id):
        # print("MEMORY session_id: ", session_id)
        # print("self.newSession_id: ", self.newSession_id)
        if session_id == None:
            if self.is_newSession == True:
                # print("\nVÀO 1")
                return []
            else:
                session_id = self.newSession_id
                # print("\nVÀO 2")
        print("MEMORY session_id SAU: ", session_id)
        traces = self.fetch_traces(session_id=session_id)
        documents_memory = []
        if len(traces) > 0:
            for trace in traces:
                if '?' not in trace.input:              # Không cần lưu câu hỏi người dùng trong memory
                    documents_memory.append(
                        {
                            'title': "Doc Memory From Session",
                            'content': trace.input,
                            'collection_date': str(datetime.today().strftime("%Y-%m-%d"))
                        }
                    )
                trace_output = trace.output.strip()
                # print('trace_outputtrace_output: ', trace_output)
                items = re.split(r'\.\s+|\.$|;\s*|\n+|:\n', trace_output)
                for item in items:        # Vì thông tin lưu vào memory nên là 1 fact <=> 1 câu... https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/memory.html
                    if item.strip() and 'Luật An Ninh Mạng 2018' not in item: 
                        documents_memory.append(
                            {
                                'title': "Doc Memory From Session",
                                'content': item.strip(),
                                'collection_date': str(datetime.today().strftime("%Y-%m-%d"))
                            }
                        )
        self.chats_memory_short_term = []
        return documents_memory
        

    def init_ragas_metrics(self, llm, embedding):
        for metric in self.metrics:
            if isinstance(metric, MetricWithLLM):
                metric.llm = llm
            if isinstance(metric, MetricWithEmbeddings):
                metric.embeddings = embedding
            run_config = RunConfig()
            metric.init(run_config)

    async def score_with_ragas(self, query, context, answer):
        scores = {}
        for m in self.metrics:   
            sample = SingleTurnSample(
                user_input=query,
                retrieved_contexts=[context],      # Ngữ cảnh RAG
                response=answer,
            )
            print("\n\nm.name: ", m.name)
            score_caculated = await m.single_turn_ascore(sample)
            scores[m.name] = score_caculated
            print("score_caculated: ", score_caculated)
            # Send scores into langfuse
            self.langfuse.score(name=m.name, trace_id=self.trace_id, value=score_caculated)
        return scores

    def fetch_traces(self, session_id: str):
        """
            input:
                session_id: str | Key của session muốn truy vấn.
            output:
                sorted_traces: list | danh sách các tracs được lấy về của session_id đó.
        """
        traces_response = self.langfuse.fetch_traces(session_id=session_id)
        traces = getattr(traces_response, "data", None)
        sorted_traces = sorted(traces, key=lambda x: x.timestamp)       # Sắp xếp lại các traces theo thứ tự thời gian các session
        return sorted_traces

    def fetch_sesions(self):
        """
            output:
                sorted_sessions: list | danh sách tất cả sessions của hôm nay.
        """
        today = datetime(datetime.now().year, datetime.now().month, datetime.now().day)  
        response = self.langfuse.fetch_sessions(
            from_timestamp=today,
            to_timestamp=datetime.now()
        )
        sessions = getattr(response, "data", None)
        sorted_sessions = sorted(sessions, key=lambda x: x.created_at, reverse=True)   # Sắp xếp lại các sessions theo thứ tự thời gian các session
        return sorted_sessions
    
    def update_current_trace(self, name, session_id, input, output):
        if session_id is None:
            if self.is_newSession:                                          # Nếu là một session mới, tạo ID mới
                self.is_newSession = False
                self.newSession_id = str(uuid.uuid4())
                session_id = self.newSession_id
                self.chats_memory_short_term = []           #########
                # print("\n\nTH1: session_id: ", session_id)
            else:                                                           # Nếu đang chat trong session mới, giữ nguyên ID
                session_id = self.newSession_id
                # print("\n\nTH2: session_id: ", session_id)
        else: 
            self.is_newSession = True                                       # Nếu đã vào một session cũ nhưng muốn tạo session mới sau này thì phải đặt lại trang thái cho is_newSession là True.. để có thể tạo session mới
            self.newSession_id = None
            # print("\n\nTH3: TẠO MỚI: ", session_id)

        if self.tmp_file_path is not None:
            # # Đọc nội dung file
            print("tmp_file_path: ", self.tmp_file_path)
            with open(self.tmp_file_path, "rb") as f:
                file_bytes = f.read()
            wrapped_obj = LangfuseMedia(
                obj=file_bytes, content_bytes=file_bytes, content_type="application/pdf"
            )

            os.remove(self.tmp_file_path)
            langfuse_context.update_current_trace(
                name=name,
                session_id=session_id,
                input=input,
                output=output,
                metadata={
                    "context": wrapped_obj
                }
            )
        else:
            self.source_file_path = None
            langfuse_context.update_current_trace(
                name=name,
                session_id=session_id,
                input=input,
                output=output,
            )

        if '?' not in input:              # Không cần lưu câu hỏi người dùng trong memory
            self.chats_memory_short_term.append(
                {
                    'title': "Doc Memory From Session",
                    'content': input,
                    'collection_date': str(datetime.today().strftime("%Y-%m-%d"))
                }
            )
        # print("output.strip(): ", output.lower())
        if 'luật' not in output.lower(): 
            items = re.split(r'\.\s+|\.$|;\s*|\n+|:\n', output.lower())
            for item in items:        # Vì thông tin lưu vào memory nên là 1 fact <=> 1 câu... https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/memory.html
                if item.strip(): 
                    self.chats_memory_short_term.append(
                        {
                            'title': "Doc Memory From Session",
                            'content': item.strip(),
                            'collection_date': str(datetime.today().strftime("%Y-%m-%d"))
                        }
                    )


    def update_observation_cost(self, model_name, input_token, output_token, cost_input, cost_output):
        """
            Hàm cập nhật chi chí theo từng token của mỗi phiên truy vấn.
        """
        langfuse_context.update_current_observation(
            model=model_name,
            usage_details={
                "input": input_token,
                "output": output_token
            },
            cost_details={
                "input": input_token*cost_input,
                "output": output_token*cost_output
            }
        )