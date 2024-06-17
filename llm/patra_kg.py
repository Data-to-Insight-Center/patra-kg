from langchain.memory import ConversationBufferWindowMemory
from langchain import hub

from prompts import CYPHER_GENERATION_TEMPLATE, QA_TEMPLATE, LLM_template
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.agents import Tool, initialize_agent
from langchain.agents import AgentExecutor, create_react_agent, load_tools
from langchain_openai import OpenAI

llm = OpenAI(temperature=0, streaming=True, api_key="")

graph = Neo4jGraph(
    url="bolt://localhost:7689", username="neo4j", password="rootroot"
)

graph.refresh_schema()



CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)
QA_GEN_TEMPLATE = PromptTemplate(
    input_variables=["context", "question"], template=QA_TEMPLATE
)
neo4jQA = GraphCypherQAChain.from_llm(
    llm=llm,
    # cypher_llm=codellama13b,
    # qa_llm=codellama13b,
    graph=graph,
    verbose=False,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    # qa_prompt=QA_GEN_TEMPLATE,
    validate_cypher=True,
)


prompt_template = PromptTemplate(input_variables=["question"], template=LLM_template)

agent_prompt = PromptTemplate(
    input_variables=["question"], template=LLM_template
)

llm_chain = LLMChain(
    llm=llm,
    prompt=prompt_template,
    verbose=True,
)

tools = [
    # Tool(
    #     name="llm",
    #     description="Use this as the last resort if none of the other tools provide an output.",
    #     func=llm_chain.run,
    # ),
    Tool(
        name = 'ICICLE_MC',
        func = neo4jQA.invoke,
        description = ( 'Use this to query about models, datasheet, deployment and their analysis. This is also referred to as ICICLE database, database, knowledge graph. If the query has a prefix IMC, parse the original query as is to this tool and return the result. Dont use any other tool after. DO NOT ALLOW DELETE, INSERT, UPDATE. say you are contacting administrator in that case. '
        )
    )
]

memory = ConversationBufferWindowMemory(k=2)

# agent = initialize_agent(
#     tools=tools,
#     llm=llm,
#     verbose=True,
#     memory=memory
# )

def get_agent_executor():
    prompt = hub.pull("hwchase17/react")
    print(prompt)
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor