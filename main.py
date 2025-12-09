from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from prompts import instructions_description, instructions_prompt
import os
from agno.utils.audio import write_audio_to_file

from agno.os import AgentOS
from agno.os.interfaces.agui import AGUI
# Read the content file
content_file_path = os.path.join(os.path.dirname(__file__), "scrapper", "get_contents", "contentfile.txt")
with open(content_file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Setup database and memory
db = SqliteDb(db_file="agno.db")
memory_manager = MemoryManager(db=db)

# Create agent
agent = Agent(
    name="Milberg Intake Assistant",
    model=OpenAIChat(
        api_key=os.getenv("OPENAI_API_KEY", "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"),
        id="gpt-4o",
        modalities=["text", "audio"],
        audio={"voice": "alloy", "format": "wav"}
    ),
    description=instructions_description(),
    instructions=instructions_prompt(content=content),
    markdown=True,
    add_datetime_to_context=True,
    timezone_identifier="Asia/Kolkata",
    user_id="website_user",
    session_id="chat_session_001",
    db=db,
    memory_manager=memory_manager,
    enable_user_memories=True,
    read_chat_history=True,
    num_history_runs=100,
)

print("Milberg Virtual Intake Assistant Ready!")
print("Type 'exit' or 'quit' to end.\n")

# while True:
#     user_input = input("You: ")
#     if user_input.lower() in ['exit', 'quit', 'bye']:
#         print("\nGoodbye!")
#         break
#     res = agent.run(user_input)
#     print(f"\nAssistant: {res.content}\n")

#     # Save audio response
#     if res.response_audio is not None:
#         write_audio_to_file(
#             audio=res.response_audio.content, 
#             filename="response.wav"
#         )



# agent_os = AgentOS(agents=[agent], interfaces=[AGUI(agent=agent)])
# app = agent_os.get_app()
# if __name__ == "__main__":
#     agent_os.serve(app="main:app", port=8000, reload=True)
