
from semantic_text_splitter import TextSplitter  # type: ignore
from llama_parse import LlamaParse # type: ignore
from llama_index.core import SimpleDirectoryReader # type: ignore
from deepgram import DeepgramClient, AnalyzeOptions
import json
import os 
from openai import OpenAI
import convertapi
import PyPDF2

client = OpenAI(api_key="",organization="org-kpRMeqZ5COwhxletMEWCNJCN")
convertapi.api_secret = 'secret_PBivDsXV3XKuxtRm'
LLAMA_PARSER_INDIVIDUAL_CACHE=True
LLAMA_PARSER_FILE_EXTRACTOR_TYPE='.pdf'
LLAMA_CLOUD_API_KEY='llx-gDpQIbSrlgFs7CckuvsJEcs2nc3fO3yEN7lloKmOHhQUNsVx'
COMPLETIONS_MODEL = "gpt-4o-mini-2024-07-18"
ARTICLE_MAX_TOKENS = 1000 #Inform Frontend if changed, being used in Add/Edit Data
ARTICLE_MIN_TOKENS = 500
LLAMA_PARSER_RESULT_TYPE='markdown'
LLAMA_PARSER_INSTRUCTIONS = """
            Parsing Instructions :- 
                Llama Parser Extraction Instructions

                Objective: Extract only the raw text data from the provided PDF document while adhering to the following guidelines:

                Ignore Text and URLs in Images: Do not extract any text or URLs that are embedded within images.
                Include URLs in Text Format: Include URLs that are present in the document as text.
                Focus on Raw Text: Extract only the plain, raw text content from the document.
                Details:

                Ignore Text and URLs in Images: Ensure that any text or URLs that appear as part of images within the document are not included in the extracted text.
                Include URLs in Text Format: Make sure to include any URLs that are part of the text content in the document.
                Extract Plain Text: Concentrate on extracting the main text content from the PDF, maintaining the original text formatting where possible but excluding any URLs or text embedded in images
            """
temp_dir = os.path.join(os.getcwd(), 'temp')
book_notes_api_key = "dc664de3a7188bfdf8a829ca324461ed8daaafcc"
deepgram = DeepgramClient(api_key=book_notes_api_key)
story = ""
system_prompt = """ You are a model designed to continue narratives based on the previous text provided. Your task is to generate the next 1-2 paragraphs while carefully following the writing style, tone, entities, tags, and storyline established so far.Consider the context of the story, including characters, settings, and plot developments, to ensure that the new paragraphs flow seamlessly from the previous ones. If the current paragraph signals the end of a chapter, provide a fitting title, heading, and initial paragraphs for the next chapter, maintaining the same style, tone, and continuity."""
summary_so_far = ""
previous_paragraph = ""

def split_documents(content:str):
    """
        Splits a text string into smaller chunks.

        This function takes a text string and splits it into smaller chunks
        using a text splitter obtained from the `get_text_splitter` function. It then returns
        a list of strings, where each string represents a chunk of text.

        Args:
            content: A text string.

        Returns:
            List[str]: A list of strings representing the split chunks of text.
    """
    # Split your data up into smaller documents with Chunks
    text_splitter = get_text_splitter()
    
    documents = text_splitter.chunks(content)
    
    # Return the list of documents as a list of strings
    return [doc for doc in documents]


def read_and_split_pdf(file_path):
    """
        Reads a PDF file and splits its content into smaller chunks.

        This function reads a PDF file located at the specified `file_path` and splits its
        content into smaller chunks using the `split_documents` function. It returns a list
        of strings, where each string represents a chunk of text extracted from the PDF.

        Args:
            file_path (str): The path to the PDF file to be read and split.

        Returns:
            List[str]: A list of strings representing the split chunks of text.
    """
    try:
        parser = LlamaParse(
            result_type=LLAMA_PARSER_RESULT_TYPE,
            parsing_instruction=LLAMA_PARSER_INSTRUCTIONS,
            invalidate_cache=LLAMA_PARSER_INDIVIDUAL_CACHE,
            api_key=LLAMA_CLOUD_API_KEY
        )
        
        file_extractor = {LLAMA_PARSER_FILE_EXTRACTOR_TYPE: parser}
        
        documents = SimpleDirectoryReader(input_files=[file_path], file_extractor=file_extractor).load_data()
        
        all_text = ""  
         
        for document in documents:
            all_text += document.text
        
        paras =  split_documents(all_text)
        
        return paras[len(paras)//2:]
    except Exception as e:
        print(e)
        return []



def get_text_splitter():
    """
        Retrieves a text splitter from lang chain for breaking down text into smaller chunks.

        This function returns a text splitter configured with the specified encoding
        name, chunk size, and chunk overlap parameters. It is used to break down large
        pieces of text into smaller chunks for processing.

        Returns:
            Semantic Text Splitter: A text splitter instance.
    """
    return TextSplitter.from_tiktoken_model(
        model=COMPLETIONS_MODEL, 
        capacity=(ARTICLE_MIN_TOKENS,ARTICLE_MAX_TOKENS)
    )

def summarizer(text,deepgram):
    TEXT =  {
    "buffer": text
    }
    options = AnalyzeOptions(
        language="en",
        summarize="v2",
        topics=True,
        intents=True,
        sentiment=True,
    )

    response = deepgram.read.analyze.v("1").analyze_text(TEXT, options)
    summary_text=response.results.summary.text
    
    return summary_text

novel_path = input("Enter the path to the novel: ")

with open(novel_path, 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    total_pages = len(pdf_reader.pages)

half_pages = total_pages // 2
split_pattern = f'0-{half_pages}'

original_file_name = os.path.basename(novel_path)

name, ext = os.path.splitext(original_file_name)

first_half_of_the_original_file = f"{name}-1-{half_pages}{ext}"

first_half_of_the_original_file_path = os.path.join(temp_dir, first_half_of_the_original_file)

if not os.path.exists(first_half_of_the_original_file_path):
    convertapi.convert('split', {
        'File': novel_path,
        'SplitByPattern': str(half_pages)
    }, from_format = 'pdf').save_files(temp_dir)
    print("Splitting the document into two halves")

paras = read_and_split_pdf(first_half_of_the_original_file_path)

eighty_percent = int(0.8 * len(paras))

if not os.path.exists(f'training_data\\{first_half_of_the_original_file}_training_data.jsonl'):
    for i in range(len(paras)):
        if i+1 == len(paras):
            break         
        story += paras[i] + '\n'
        summary = summarizer(story,deepgram)
        
        summary_so_far = summary
        previous_paragraph = paras[i]
        
        user_prompt = f"Summary : {summary} \n\n Previous Paragraph : {paras[i]}"
        assistant_response = paras[i+1]
        
        
        json_obj = {"messages":[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt},{"role":"assistant","content":assistant_response}]}
        
        if i < eighty_percent:
            with open(f'training_data\\{first_half_of_the_original_file}_training_data.jsonl', 'a') as f:
                f.write(json.dumps(json_obj, separators=(',', ':')) + '\n')
        else:
            with open(f'testing_data\\{first_half_of_the_original_file}_testing_data.jsonl', 'a') as f:
                f.write(json.dumps(json_obj, separators=(',', ':')) + '\n')
        
        print(f"Completed {i+1} iterations out of {len(paras)-1}")
    
# Upload the file for fine-tuning
training_file = client.files.create(
    file=open(f"training_data\\{first_half_of_the_original_file}_training_data.jsonl", "rb"),
    purpose="fine-tune"
)

testing_file = client.files.create(
    file=open(f"testing_data\\{first_half_of_the_original_file}_testing_data.jsonl", "rb"),
    purpose="fine-tune"
)

# Create a fine-tuning job
job = client.fine_tuning.jobs.create(
    training_file=training_file.id,
    validation_file=testing_file.id,
    model=COMPLETIONS_MODEL,
    suffix="novel_generation_model"
)

param_file_tune_job_id = job.id

### Retrieve the state of a fine-tune
client.fine_tuning.jobs.retrieve(param_file_tune_job_id)

### Loop
# Retrieve the state of a fine-tune and wait till sucess
from time import sleep
while client.fine_tuning.jobs.retrieve(param_file_tune_job_id).status != 'succeeded':
  print(client.fine_tuning.jobs.retrieve(param_file_tune_job_id).status,"Waiting for the fine-tuning to complete")
  sleep(10)

print("Fine-tuning completed successfully")

### model from completed job
param_file_tune_model = client.fine_tuning.jobs.retrieve(param_file_tune_job_id).fine_tuned_model

print("This is your fine tuned model name :- \n",param_file_tune_model,'\n\n')
print("This is the summary so far :- \n",summary_so_far,'\n\n')
print("This is the previous paragraph :- \n",previous_paragraph,'\n\n')

with open(f'{first_half_of_the_original_file}_fine_tunning_details.txt', 'w') as f:
    f.write(f"This is your fine tuned model name :- \n{param_file_tune_model}\n\n")
    f.write(f"This is the summary so far :- \n{summary_so_far}\n\n")
    f.write(f"This is the previous paragraph :- \n{previous_paragraph}\n\n")