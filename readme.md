## This repo contains plug and play scripts for novel generation 


## Steps for installation 

1.) Create virtual environment and activate it

```
python -m venv venv && venv\Scripts\activate
```

2.) Install Dependencies 

```
pip install -r requirements.txt
```

3.)Create three folders in the root directory named : temp , training_data and testing_data

4.)Add open ai api key in both the scripts 


5.) Run auto_training.py

```
python automate_training.py
```

This file generates jsonl file for training and fine tunes open ai model. 

## Inputs : 

novel_path : Relative or Absolute path either is fine 

## Outputs : 

fine tuned model name 

summary of the first half 

last paragraph on which the model was trained on .


6.)Retrieve the name of the fine tuned model either from the generated txt file or the terminal

7.) Run auto_para_generation.py
```
python auto_para_generation.py
```

This file generates the next paragraph and updates the given summary . 

## Inputs : 

fine_tuned_model_name 

novel_name 

initial_paragraph 

summary_so_far

## Output : 

Updated Summary 

New paragraph