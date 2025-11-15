import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict
load_dotenv()

SUMMARIZE_THRESHOLD = 20

client = OpenAI(
    api_key = os.environ.get("DEEPSEEK_API_KEY"),
    base_url = "https://api.deepseek.com/v1",
)

class SummarizationMemory:
    def __init__(self, system_prompt: str="You are a shop assitant. you have multiple function calls to use, and you should help the user to achieve their goals."):
        self.summary = ""
        self._original_system_prompt = {"role":"system","content":system_prompt}
        self.short_term_history = [{"role": "system", "content":system_prompt}]

    def _generate_summary(self,messages: List[Dict]) -> str:
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        summary_prompt = f"""
        Please summarize the following conversation into a concise summary.
        The aim of the summarization is to remind yourself of the previous information.
        Please pay more attention on the product that the user has talked about.
        Please write the summary in a third-person perspective, like:"The user asked to find a phone, and a product 'phone' was found with product_id:1, stock:100, price:100."
        ---- Conversation history messages ----
        {conversation_text}
        ---- Please output the summary here ----
        """

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": summary_prompt}],
                temperature=0.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error during summarization: {e}"

        
    def add_message(self, message: Dict):
        self.short_term_history.append(message)
        if len(self.short_term_history) > SUMMARIZE_THRESHOLD:
            NUM_TO_KEEP = 6
            messages_to_summarize = self.short_term_history[1:-NUM_TO_KEEP]
            new_summary_part = self._generate_summary(messages_to_summarize)

            new_history = [
                self._original_system_prompt,
                {"role":"system","content":f"You have done several conversations before, and this is the summarization of the previous conversations: {new_summary_part}"},
                *self.short_term_history[-NUM_TO_KEEP:],
            ]
            self.short_term_history = new_history

    def get_history(self):
        return self.short_term_history