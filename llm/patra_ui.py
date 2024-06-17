import streamlit as st
from langchain.callbacks.streamlit import StreamlitCallbackHandler
from patra_kg import get_agent_executor

agent_executor = get_agent_executor()

if prompt := st.chat_input():
    st.chat_message("user").write(prompt)
    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        response = agent_executor.invoke(
            {"input": prompt}, {"callbacks": [st_callback]}
        )
        st.write(response["output"])