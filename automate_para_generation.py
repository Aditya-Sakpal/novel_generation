import openai
import os 
import csv
from deepgram import DeepgramClient, AnalyzeOptions
import json

openai.api_key = ""
book_notes_api_key = "dc664de3a7188bfdf8a829ca324461ed8daaafcc"

fine_tuned_model = input("Enter the fine tuned model name: ")

novel_name = input("Enter the name of the novel: ")

deepgram = DeepgramClient(api_key=book_notes_api_key)

options = AnalyzeOptions(
    language="en",
    summarize="v2",
    topics=True,
    intents=True,
    sentiment=True,
)


SYSTEM_PROMPT_FOR_WRITING_STYLE = """
    You are a literary analysis assistant tasked with determining the writing style, tone, and characteristics of novel writers based on provided text samples. 
    Your analysis should be accurate, providing clear and concise feedback. Deliver the results in a structured JSON format containing the following 
    keys: `writing_style`, `tone`, and `characteristics`. Ensure the `writing_style` and `tone` fields provide an appropriate name, and the `characteristics` field 
    lists notable features of the writing style.
"""

USER_PROMPT_FOR_WRITING_STYLE = """
    Analyze the following paragraph and provide a JSON output with the `writing_style`, `tone`, and `characteristics` of the novel writer's style:

    Input Paragraph:
    {previous_paragraph}

    Please determine the following:
    - Name of the writing style
    - Name of the tone
    - A few characteristics of the writing style

    Ensure the output is in the following JSON format:

    {{
        "writing_style": "Name of the writing style",
        "tone": "Name of the tone",
        "characteristics": ["Characteristic 1", "Characteristic 2", "Characteristic 3"]
    }}
"""
SYSTEM_PROMPT = """
    You are a model designed to continue narratives based on the previous text provided. 
    Your task is to generate the next 1-2 paragraphs, ensuring continuity with the given writing style, tone, and characteristics of the text. 
    If the writing style, tone, and characteristics are unknown, you may deduce them from the provided text. 
    Consider the context of the story and determine if the current paragraph is the end of a chapter. If it's the end of a chapter, provide a title, 
    heading, and initial paragraphs for the next chapter, maintaining the same style and tone.
"""

USER_PROMPT = """
    Summary: 
    {summary_text}

    Previous Paragraph:
    {story_so_far}

    Writing Style: {writing_style} (if known, else determine from the provided text)
    Tone: {tone} (if known, else determine from the provided text)
    Characteristics: {characteristics} (if known, else determine from the provided text)

    Please generate the next paragraphs using the provided information.
"""


def querying(story_so_far,previous_paragraph):
    
    TEXT =  {
        "buffer": story_so_far
    }
    
    response = deepgram.read.analyze.v("1").analyze_text(TEXT, options)
    
    summary_text=response.results.summary.text
    
    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content":SYSTEM_PROMPT_FOR_WRITING_STYLE },
            {"role": "user", "content": USER_PROMPT_FOR_WRITING_STYLE.format(previous_paragraph=previous_paragraph)}
        ]
    )
    
    response = completion.choices[0].message.content

    try:
        response = json.loads(response)      
        writing_style,tone,characteristics = response['writing_style'],response['tone'],response['characteristics']
    except Exception as e:
        writing_style,tone,characteristics = 'Unknown','Unknown',['Unknown']
    
    completion = openai.chat.completions.create(
        model=fine_tuned_model,
        messages=[
            {"role": "system", "content":SYSTEM_PROMPT },
            {"role": "user", "content": USER_PROMPT.format(summary_text=summary_text,story_so_far=story_so_far,writing_style=writing_style,tone=tone,characteristics=characteristics)} 
        ]
    )
    
    response = completion.choices[0].message.content
    
    header = ["Previous Paragraph", "Updated Summary", "Next Paragraph"]
    data = [story_so_far, summary_text,response]
    
    if not os.path.exists(f'{novel_name}_results.csv'):
        with open(f'{novel_name}_results.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(data)
    else:
        with open(f'{novel_name}_results.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data)
    
    story_build_up = story_so_far + response
    
    return story_build_up , response

while True:
    intitial_previous_paragraph = input("Enter the initial paragraph: ")
    summary_of_the_story_so_far = input("Enter the summary of the story so far: ")


    summary_of_the_story_so_far,new_paragraph = querying(summary_of_the_story_so_far,intitial_previous_paragraph)


    print(f"Summary of the story so far: {summary_of_the_story_so_far}\n\n")
    print(f"New Paragraph: {new_paragraph}\n\n")    