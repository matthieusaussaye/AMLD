import streamlit as st
from typing import Literal
from dataclasses import dataclass
from langchain.memory import ConversationBufferMemory
from langchain.callbacks import get_openai_callback
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.prompts.prompt import PromptTemplate
from prompts.prompts import templates
# Audio
from audio_recorder_streamlit import audio_recorder
from IPython.display import Audio
from app_utils import convert, convert_openai, save_wav_file
import openai
import tempfile
from PIL import Image

### ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

OPENAI_API_KEY = ""

home_title = "AI Vocal Agent - Prototype"

with st.sidebar:
    st.markdown("AMLD - AI Vocal Agent Workshop 2024")
    im = Image.open("appliedmldays_logo.jpeg")
    st.image(im, width=250)
    im2 = Image.open("pulse_partners.png")
    st.image(im2, width=250)


st.markdown(
    "<style>#MainMenu{visibility:hidden;}</style>",
    unsafe_allow_html=True
)
st.markdown(f"""# {home_title} <span style=color:#2E9BF5><font size=5>Beta</font></span>""", unsafe_allow_html=True)

st.markdown("""\n""")
# st.markdown("#### Greetings")
st.markdown("""\n""")

st.markdown("#### Dites-nous ce que vous pensez des assurances:")

### ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
@dataclass
class Message:
    """class for keeping track of interview history."""
    origin: Literal["human", "ai"]
    message: str
def initialize_session_state_jd():
    """ initialize session states """
    if 'jd_memory' not in st.session_state:
        st.session_state.jd_memory = ConversationBufferMemory()
    # interview history
    if "jd_history" not in st.session_state:
        st.session_state.jd_history = []
        st.session_state.jd_history.append(Message("ai",
                                                   "Si vous deviez conclure une nouvelle assurance vie (3e pilier), auprès de quelle entreprise le feriez-vous ? Citez le nom de l’entreprise et expliquez pourquoi."))
    # token count
    if "token_count" not in st.session_state:
        st.session_state.token_count = 0
    # llm chain and memory
    if "jd_screen" not in st.session_state:
        llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY,
                         model_name="gpt-4-turbo-preview",
                         temperature=0.8)
        PROMPT = PromptTemplate(
            input_variables=["history", "input"],
            template=templates.base_template)

        st.session_state.jd_screen = ConversationChain(prompt=PROMPT,
                                                       llm=llm,
                                                       memory=st.session_state.jd_memory)
    if 'jd_feedback' not in st.session_state:
        llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY,
                         model_name="gpt-4-turbo-preview",
                         temperature=0.8)
        st.session_state.jd_feedback = ConversationChain(
            prompt=PromptTemplate(input_variables=["history", "input"], template=templates.feedback_template),
            llm=llm,
            memory=st.session_state.jd_memory,
        )


def answer_call_back():
    with get_openai_callback() as cb:
        # user input
        human_answer = st.session_state.answer
        # transcribe audio
        if voice:
            save_wav_file("temp/audio.wav", human_answer)
            try:
                input = convert("temp/audio.wav")
                # save human_answer to history
            except:
                st.session_state.jd_history.append(Message("ai",
                                                           "Sorry, I didn't get that."))
                return "Please try again."
        else:
            input = human_answer

        st.session_state.jd_history.append(
            Message("human", input)
        )
        # OpenAI answer and save to history
        llm_answer = st.session_state.jd_screen.run(input)
        # speech synthesis and speak out
        audio_file_path = convert_openai(llm_answer)
        # create audio widget with autoplay
        audio_widget = Audio(audio_file_path, autoplay=True)
        # save audio data to history
        st.session_state.jd_history.append(
            Message("ai", llm_answer)
        )
        st.session_state.token_count += cb.total_tokens
        return audio_widget


### ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
# initialize session states
initialize_session_state_jd()
# st.write(st.session_state.jd_guideline)
credit_card_placeholder = st.empty()
col1, col2 = st.columns(2)
with col1:
    feedback = st.button("Get Interview Feedback")

chat_placeholder = st.container()
answer_placeholder = st.container()
audio = None
# if submit email adress, get interview feedback imediately

if feedback:
    evaluation = st.session_state.jd_feedback.run("please give evaluation regarding the interview")
    st.markdown(evaluation)
    st.download_button(label="Download Interview Feedback", data=evaluation, file_name="interview_feedback.txt")
    st.stop()
else:
    with answer_placeholder:
        voice: bool = st.checkbox("Utiliser mon micro pour répondre")
        if voice:
            answer = audio_recorder(pause_threshold=2.5, sample_rate=44100)
            # st.warning("An UnboundLocalError will occur if the microphone fails to record.")
        else:
            answer = st.chat_input("Your answer")
        if answer:
            st.session_state['answer'] = answer
            audio = answer_call_back()
    with chat_placeholder:
        for answer in st.session_state.jd_history:
            if answer.origin == 'ai':

                if audio:
                    with st.chat_message("assistant"):
                        st.write(answer.message)
                        st.write(audio)
                else:
                    with st.chat_message("assistant"):
                        st.write(answer.message)
            else:
                with st.chat_message("user"):
                    st.write(answer.message)

    credit_card_placeholder.caption(f"""Progress: {int(len(st.session_state.jd_history) / 30 * 100)}% completed.""")
