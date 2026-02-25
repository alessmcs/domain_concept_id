import contextlib
import json
import sys
import os

import sys
print("SYS EXECUTABLE:")
print(sys.executable)

import time
from torch import cat as torch_cat, tensor as torch_tensor, tensor, long as torch_long, device as torch_device
import pandas as pd
import xmiParser as xp
import re

# Make sure we can import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local imports
from prompt_templates import (
    prompt, 
    prompt_uq, # The function that creates the user portion of the prompt
    attribute_prompt,  # The function that creates the user portion of the attribute prompt
    method_prompt,  # The function that creates the user portion of the method prompt
    association_prompt,  # The function that creates the user portion of the association prompt
    llama_template,
    review_classification_system_prompt,
    attr_classification_system_prompt,
    method_classification_system_prompt
)
from config import ExLlamaArguments

import exllamav2
from exllamav2 import (
    ExLlamaV2,
    ExLlamaV2Config,
    ExLlamaV2Cache,
    ExLlamaV2Tokenizer
)
from exllamav2.generator import (
    ExLlamaV2DynamicGenerator,
    ExLlamaV2DynamicJob,
    ExLlamaV2Sampler
)

from exllamav2.util import get_basic_progress


#### LETS TRY BATCH PROMPTING
def batch_classify_classes(json_data, model_args, tokenizer, generator):
    batch_size = 5 # 10 classes at a time 

    domain_specific = []
    implementation_detail = []
    confidence_scores = {}

    base_gen_settings = ExLlamaV2Sampler.Settings(
        token_repetition_penalty=model_args.gen_settings[0],
        temperature=model_args.gen_settings[1],
    )

    readme = json_data.get("readme", "")
    ranked_classes = json_data.get("ranked_classes", [])

    # Calculate number of batches correctly
    num_batches = (len(ranked_classes) + batch_size - 1) // batch_size

    with get_basic_progress() as progress: 
        # FIX: Use correct total for progress tracking
        task_id = progress.add_task("Processing batches...", total=num_batches, name="Batch Processing")
        processed_count = 0

        for i in range(0, len(ranked_classes), batch_size):
            user_prompt = batch_class_prompt(readme, 
                                             domain_specific,
                                             implementation_detail,
                                             ranked_classes[i:i + batch_size])
            
            input_prompt = llama_template.format(
                system_prompt=review_classification_system_prompt,
                user_prompt=user_prompt
            )

            input_ids = tokenizer.encode(input_prompt)

            job = ExLlamaV2DynamicJob(
                input_ids=input_ids,
                gen_settings=base_gen_settings,
                max_new_tokens=model_args.max_new_tokens,
                stop_conditions=[tokenizer.single_id("<|eot_id|>")],
                token_healing=True,
                identifier=i,  # Unique identifier for this job
            )

            generator.enqueue(job)  # Enqueue the job

            job_processed = False
            while not job_processed:
                results = generator.iterate()
                for result in results:
                    # Check if this is the job we just enqueued
                    if result.get("identifier") == i and result["eos"]:
                        response = result["full_completion"]

                        print(response) 
                        
                        # REMOVE EXPENSIVE DEBUG PRINTS:
                        # print(result)
                        # print(response)
                        
                        print(f"✓ Processed batch {processed_count + 1}/{num_batches}")
                        
                        results_map = extract_batch_classification(response)

                        # FIX: Correct unpacking of results
                        for class_name in results_map:
                            classification_str, confidence = results_map[class_name]  # Unpack tuple correctly
                            
                            if classification_str in ("domain-specific", "domain", "domainspecific"):
                                domain_specific.append(class_name)
                                confidence_scores[class_name] = confidence if confidence else None
                                print(f"✓ {class_name}: Domain-specific")
                            elif classification_str in ("implementation", "implementationdetail", "non-domainspecific"):
                                implementation_detail.append(class_name)
                                confidence_scores[class_name] = confidence if confidence else None
                                print(f"✓ {class_name}: Implementation")

                        job_processed = True
                        processed_count += 1
                        progress.update(task_id, advance=1)
                        break

    generator.clear_queue()

    json_data["classifications"] = {
        "Domain-specific": domain_specific,
        "Implementation detail": implementation_detail,
        "Confidence Scores": confidence_scores,
        "prompt_used": user_prompt
    }

    print(f"Classified {len(domain_specific)} as Domain-specific and {len(implementation_detail)} as Implementation detail.")
    print("Classification complete.")
    return json_data


def extract_batch_classification(response_text):
    """
    Extracts the classification and class names from the LLM response.
    Expected JSON structure in the LLM response:

        {
            "classifications": [
                {"class": "someClassName", "classification": "Domain-specific", "probability": 0.95},
                {"class": "anotherClassName", "classification": "Implementation detail", "probability": 0.85}
            ]
        }

    Returns:
        list: List of tuples (class_name, classification_str, confidence)
    """
    try:
        json_match = re.search(r"\{.*?\}", response_text, re.DOTALL)
        if not json_match:
            print("Warning: No JSON-like structure found in the response.")
            return []

        json_text = json_match.group(0)
        response_data = json.loads(json_text)

        if "classifications" in response_data:
            results = {}
            for item in response_data["classifications"]:
                if "class" in item and "classification" in item:
                    class_name = item["class"]
                    classification = item["classification"].lower().replace(" ", "")
                    confidence = item.get("probability", None)
                    results[class_name] = (classification, confidence)
            return results

    except json.JSONDecodeError:
        print("Warning: Failed to parse JSON response.")
    except Exception as e:
        print(f"Error during classification extraction: {e}")

    return []
        

def extract_classification(response_text):
    """
    Extracts the classification and class name from the LLM response.
    Expected JSON structure in the LLM response:

        {
            "class": "someClassName",
            "classification": "Domain-specific",
        }

    Returns:
        tuple: (class_name, classification_str)
    """
    print("response text ", response_text)
    try:
        json_match = re.search(r"\{.*?\}", response_text, re.DOTALL)
        if not json_match:
            print("Warning: No JSON-like structure found in the response.")
            return None, None

        json_text = json_match.group(0)
        response_data = json.loads(json_text)

        if "class" in response_data and "classification" in response_data:
            class_name = response_data["class"]
            # Normalize classification strings
            classification = response_data["classification"].lower().replace(" ", "")
            if "probability" in response_data:
                confidence = response_data["probability"]
                return class_name, classification, confidence
            else:
                return class_name, classification

    except json.JSONDecodeError:
        print("Warning: Failed to parse JSON response.")
    except Exception as e:
        print(f"Error during classification extraction: {e}")

    return None, None

# TODO! 
def extract_attr_classification(response_text):
    print("response text ", response_text)
    try:
        json_match = re.search(r"\{.*?\}", response_text, re.DOTALL)
        if not json_match:
            print("Warning: No JSON-like structure found in the response.")
            return None, None

        json_text = json_match.group(0)
        response_data = json.loads(json_text)

        if "attribute" in response_data and "classification" in response_data:
            attr_raw = response_data["attribute"]
            if isinstance(attr_raw, (list, tuple)):
                # If it's a tuple/list, take the first element (attribute name)
                attr_name = attr_raw[0]
                # If the second element exists, use it as the attribute type
            else:
                # If it's already a string, use it directly
                attr_name = attr_raw
            # Normalize classification strings
            classification = response_data["classification"].lower().replace(" ", "")
            # rationale = response_data["rationale"]
            return attr_name, classification #rationale

    except json.JSONDecodeError:
        print("Warning: Failed to parse JSON response.")
    except Exception as e:
        print(f"Error during classification extraction: {e}")

    return None, None

def extract_method_classification(response_text):
    print(response_text)
    try:
        json_match = re.search(r"\{.*?\}", response_text, re.DOTALL)
        if not json_match:
            print("Warning: No JSON-like structure found in the response.")
            return None, None

        json_text = json_match.group(0)
        response_data = json.loads(json_text)

        if "method" in response_data and "classification" in response_data:
            method_name = response_data["method"]
            # Normalize classification strings
            classification = response_data["classification"].lower().replace(" ", "")
            # rationale = response_data["rationale"]
            return method_name, classification #

    except json.JSONDecodeError:
        print("Warning: Failed to parse JSON response.")
    except Exception as e:
        print(f"Error during classification extraction: {e}")

    return None, None

def extract_association_classification(response_text):
    try:
        json_match = re.search(r"\{.*?\}", response_text, re.DOTALL)
        if not json_match:
            print("Warning: No JSON-like structure found in the response.")
            return None, None

        json_text = json_match.group(0)
        response_data = json.loads(json_text)

        if "should_associate" in response_data and "association_type" in response_data:
            should_associate = response_data["should_associate"]
            association_type = response_data["association_type"]
            # rationale = response_data["rationale"]
            
            return should_associate, association_type #rationale

    except json.JSONDecodeError:
        print("Warning: Failed to parse JSON response.")
    except Exception as e:
        print(f"Error during classification extraction: {e}")

    return None, None, None

def load_exllama_model(model_args):
    """
    Loads the ExLlamaV2 model, tokenizer, and generator once.
    Returns (model, tokenizer, generator).
    """
    print("Loading ExLlamaV2 config...")
    config = ExLlamaV2Config(model_args.model_dir)

    #config = ExLlamaV2Config(model_args)

    import gc
    import torch
    gc.collect()
    torch.cuda.empty_cache()

    config.arch_compat_overrides()

    print("Loading model...")
    model = ExLlamaV2(config)

    print("Creating cache...")
    cache = ExLlamaV2Cache(model, max_seq_len=model_args.max_seq_len, lazy=True)

    print("Loading model splits...")
    model.load_autosplit(cache, progress=True)

    print("Loading tokenizer...")
    tokenizer = ExLlamaV2Tokenizer(config)

    print("Initializing generator...")
    generator = ExLlamaV2DynamicGenerator(
        model=model,
        cache=cache,
        tokenizer=tokenizer #,
        # max_batch_size=model_args.max_batch_size,
        # max_q_size=model_args.max_q_size
    )

    return model, tokenizer, generator

def build_prompt_ids(tokenizer, parts):
    """
    parts: list of strings (already split into static and dynamic parts)
    returns: torch.Tensor [1, seq_len] on CPU
    """

    # print("PARTTS")
    # for p in parts: print(p)

    all_ids = []
    for p in parts:
        all_ids.extend(p)  # append into one big list

    #print(all_ids)

    
    return tensor([all_ids], dtype=torch_long, device=torch_device("cpu"))


def classify_classes(json_data, model_args, tokenizer, generator):
    """
    Classify tokenized class names as either Domain-specific or Implementation detail.
    Uses the ExLlamaV2 model and the supplied prompt templates.

    Args:
        json_data (dict): Contains 'ranked_classes', 'readme', etc.
        model_args (ExLlamaArguments): Model configuration arguments.

    Returns:
        dict: Updated JSON data with "classifications" and "prompt_used".
    """

    # Prepare two lists to hold classification results
    domain_specific = []
    implementation_details = []
    confidence_scores = {}

    # generation settings used for all classifications
    base_gen_settings = ExLlamaV2Sampler.Settings(
        token_repetition_penalty=model_args.gen_settings[0],
        temperature=model_args.gen_settings[1],
    )

    # Retrieve data from JSON
    readme = json_data.get("readme", "")
    ranked_classes = json_data.get("ranked_classes", [])
    # testing 1 class to avoid waiting for all classes to be classified
    # ranked_classes = ranked_classes[:1]

    # 1) We open a progress context
    # Enqueuing all the jobs & prompts first so we can directly classify them in one go 
    with get_basic_progress() as progress:
        # 2) Create a progress task
        #    The 'total' is how many classes we're going to classify.

        task_id = progress.add_task(
            "[green]Enqueuing classes...",
            total=len(ranked_classes),
            name="Queue adding Progress"
        )

        processed_count = 0

        # Classify each class name in a sequential loop
        for i, tokenized_name in enumerate(ranked_classes):
            # print(f"Enqueuing class {i + 1}/{len(ranked_classes)}: {tokenized_name}")
            user_prompt = prompt_uq(
                readme=readme,
                domain_specific=domain_specific,
                implementation_details=implementation_details,
                tokenized_name=tokenized_name
            )

            # Combine system + user to create final prompt
            input_prompt = llama_template.format(
                system_prompt=review_classification_system_prompt,
                user_prompt=user_prompt
            )

            input_ids = tokenizer.encode(input_prompt)


            # # print("Token IDs:", input_ids[0])
            # decoded_text = tokenizer.decode(input_ids)
            # print("DECODED", decoded_text)


            # Ensure it doesnt exceed max length
            # if input_ids.shape[1] > model_args.max_seq_len:
            #     print(f"Warning: Input prompt for '{tokenized_name}' exceeds max length ({len(input_ids)} > {model_args.max_seq_len})")
            #     input_ids = input_ids[:model_args.max_seq_len]

            # Create a new job
            job = ExLlamaV2DynamicJob(
                input_ids=input_ids,
                gen_settings=base_gen_settings,
                max_new_tokens=model_args.max_new_tokens,
                stop_conditions=[tokenizer.single_id("<|eot_id|>")],
                token_healing=True,
                identifier=i,  # Unique identifier for this job
            )

            generator.enqueue(job)  # Enqueue the job

            # Wait for generation to complete
            job_processed = False
            while not job_processed:
                results = generator.iterate()
                for result in results:
                    # Check if this is the job we just enqueued
                    if result.get("identifier") == i and result["eos"]:
                        response = result["full_completion"]
                        print(result)
                        print(response)
                        class_name, classification_str, confidence = extract_classification(response)
                        
                        if class_name and classification_str:
                            if classification_str in ("domain-specific", "domain", "domainspecific"):
                                domain_specific.append(class_name)
                                print(f"Classified '{class_name}' as Domain-specific.")
                            elif classification_str in ("implementation", "implementationdetail", "non-domainspecific"):
                                implementation_details.append(class_name)
                                print(f"Classified '{class_name}' as Implementation detail.")
                        confidence_scores[class_name] = confidence if confidence else None
                        job_processed = True
                        processed_count += 1
                        progress.update(task_id, advance=1)
                        break
    
    generator.clear_queue()

    # print(f"Beginning classification of {len(ranked_classes)} classes...")

    # # Now generate responses for all enqueued jobs
    # with get_basic_progress() as progress: 
            
    #     task_id = progress.add_task(
    #     "[green]Classifying classes...",
    #     total=len(ranked_classes),
    #     name="Classification Progress"
    #     )

    #     while generator.num_remaining_jobs():
    #         results = generator.iterate() # use iterate() to get token by token results, for each class. 
    #         for result in results:
    #             if not result["eos"]:
    #                 continue  # Not done generating for this job

    #             response = result["full_completion"]
    #             # added print below for debugging
    #             # print(f"Prompt:\n{input_prompt}\n\n ###======================== this is the response ===================###\n Response:\n{response}\n ###==================== end of response =============### ")
    #             class_name, classification_str = extract_classification(response)
    #             if class_name and classification_str:
    #                 if classification_str in ("domain-specific", "domain", "domainspecific"):
    #                     domain_specific.append(class_name)
    #                     # print(f"Classified '{class_name}' as Domain-specific.")
    #                     # print(f"Raw Response: {response}")
    #                     with open("/u/mancasat/Desktop/summer_intern/domain-concepts-identification-using-LLMs-aless/src/model_logic.txt", "a") as f:
    #                         print(response, file=f)
    #                 elif classification_str in ("implementation", "implementationdetail", "non-domainspecific"):
    #                     implementation_details.append(class_name)
    #                     # print(f"Classified '{class_name}' as Implementation detail.")
    #                     # print(f"Raw Response: {response}")
    #                     with open("/u/mancasat/Desktop/summer_intern/domain-concepts-identification-using-LLMs-aless/src/model_logic.txt", "a") as f:
    #                         print(response, file=f)
    #                 else:
    #                     print(f"Warning: Classification not recognized for '{tokenized_name}'.")
    #                     print(f"Raw Response: {response}")
    #             else:
    #                 print(f"Warning: Failed to classify '{tokenized_name}'. Raw Response: {response}")
    #             progress.update(task_id, advance=1)

    # generator.clear_queue() # Clear out the generator queue after processing all jobs

    # ------------------------ UPDATE JSON DATA ------------------------
    json_data["classifications"] = {
        "Domain-specific": domain_specific,
        "Implementation detail": implementation_details,
        "Confidence Scores": confidence_scores,
        "prompt_used": user_prompt  # This will be updated later with the final prompt used
    }

    print(f"Classified {len(domain_specific)} as Domain-specific and {len(implementation_details)} as Implementation detail.")
    
    # Keep track of the final (system+user) prompt template for reference
    #json_data["prompt_used"] = user_prompt

    print("Classification complete.")
    return json_data

def reclassify_classes(json_data, model_args, tokenizer, generator): 
    """
    Re-classify the positive classes 
    Uses the ExLlamaV2 model and the supplied prompt templates.

    Args:
        json_data (dict): Contains 'ranked_classes', 'readme', etc.
        model_args (ExLlamaArguments): Model configuration arguments.

    Returns:
        dict: Updated JSON data with "classifications" and "prompt_used".
    """

    # Prepare two lists to hold classification results
    domain_specific = []
    implementation_details = []

    # generation settings used for all classifications
    base_gen_settings = ExLlamaV2Sampler.Settings(
        token_repetition_penalty=model_args.gen_settings[0],
        temperature=model_args.gen_settings[1],
    )

    # Retrieve data from JSON
    readme = json_data.get("readme", "")
    ranked_classes = json_data.get("ranked_classes", [])
    # testing 1 class to avoid waiting for all classes to be classified
    # ranked_classes = ranked_classes[:1]

    # 1) We open a progress context
    # Enqueuing all the jobs & prompts first so we can directly classify them in one go 
    with get_basic_progress() as progress:
        # 2) Create a progress task
        #    The 'total' is how many classes we're going to classify.

        task_id = progress.add_task(
            "[green]Enqueuing classes...",
            total=len(ranked_classes),
            name="Queue adding Progress"
        )

        processed_count = 0

        # Classify each class name in a sequential loop
        for i, tokenized_name in enumerate(ranked_classes):
            # print(f"Enqueuing class {i + 1}/{len(ranked_classes)}: {tokenized_name}")
            user_prompt = prompt(
                readme=readme,
                domain_specific=domain_specific,
                implementation_details=implementation_details,
                tokenized_name=tokenized_name
            )

            # Combine system + user to create final prompt
            input_prompt = llama_template.format(
                system_prompt=review_classification_system_prompt,
                user_prompt=user_prompt
            )

            input_ids = tokenizer.encode(input_prompt)

            # Create a new job
            job = ExLlamaV2DynamicJob(
                input_ids=input_ids,
                gen_settings=base_gen_settings,
                max_new_tokens=model_args.max_new_tokens,
                stop_conditions=[tokenizer.single_id("<|eot_id|>")],
                token_healing=True,
                identifier=i,  # Unique identifier for this job
            )

            generator.enqueue(job)  # Enqueue the job

            # Wait for generation to complete
            job_processed = False
            while not job_processed:
                results = generator.iterate()
                for result in results:
                    # Check if this is the job we just enqueued
                    if result.get("identifier") == i and result["eos"]:
                        response = result["full_completion"]
                        print(result)
                        print(response)
                        class_name, classification_str = extract_classification(response)
                        
                        if class_name and classification_str:
                            if classification_str in ("domain-specific", "domain", "domainspecific"):
                                domain_specific.append(class_name)
                                print(f"Classified '{class_name}' as Domain-specific.")
                            elif classification_str in ("implementation", "implementationdetail", "non-domainspecific"):
                                implementation_details.append(class_name)
                                print(f"Classified '{class_name}' as Implementation detail.")
                        job_processed = True
                        processed_count += 1
                        progress.update(task_id, advance=1)
                        break
    
    generator.clear_queue()


    # ------------------------ UPDATE JSON DATA ------------------------
    json_data["classifications"] = {
        "Domain-specific": domain_specific,
        "Implementation detail": implementation_details,
        "prompt_used": user_prompt  # This will be updated later with the final prompt used
    }

    print(f"Reclassified {len(domain_specific)} as Domain-specific and {len(implementation_details)} as Implementation detail.")
    
    # Keep track of the final (system+user) prompt template for reference
    #json_data["prompt_used"] = user_prompt

    print("Relassification complete.")
    return json_data

# TODO: for now dont pass the types in the relevant/irrelevant lists, but after testing performance try it WITH the types passed there and compare 
# its easy just edit the output in extract_attr_classification to return the type as well and append it to the relevant/irrelevant lists
def classify_attributes(curr_class, tokenized_class_names, attributes, readme, neighboring_classes, model_args, tokenizer, generator):
    """
    Classify attributes as relevant or irrelevant for a given class.
    Uses the ExLlamaV2 model and the supplied prompt templates.

    Args:
        tokenized_class_name (str): The name of the class being classified.
        attributes (list): List of attributes to classify.
        readme (str): The README content for context.
        neighboring_classes (list): List of neighboring classes for context.
        model_args (ExLlamaArguments): Model configuration arguments.
        tokenizer (ExLlamaV2Tokenizer): Tokenizer instance.
        generator (ExLlamaV2DynamicGenerator): Generator instance.

    Returns:
        dict: Classification results with "Relevant" and "Irrelevant" attributes.
    """
    
    relevant_attrs = []
    irrelevant_attrs = []

    # rationales = {}

    return_data = {
        "classifications":{},
        # "rationales": {},
        "prompt_used": ""
    }

    # generation settings used for all classifications
    base_gen_settings = ExLlamaV2Sampler.Settings(
        token_repetition_penalty=model_args.gen_settings[0],
        temperature=model_args.gen_settings[1],
    )

    # TODO: maybe we dont even need the tokenized class names, maybe the original class name will be ok  


    tokenized_neighbors = {}

    # "type" is the kind of relationship (e.g., "association", "generalization"...)
    for type in neighboring_classes:
        if type not in tokenized_neighbors:
            tokenized_neighbors[type] = {}  # FIX: Use DICT, not list
        
        for c in neighboring_classes[type]:
            if c not in tokenized_neighbors[type]:  # FIX: Check within the type dict
                tokenized_neighbors[type][c] = []  # Now this works
            if c in tokenized_class_names:
                tokenized_neighbors[type][c].append(tokenized_class_names[c])

    full_prompt = ""

    with get_basic_progress() as progress:
        # The 'total' is how many classes we're going to classify.

        print(curr_class)

        task_id = progress.add_task(
            "[green]Enqueuing attributes...",
            total=len(attributes),
            name="Queue adding Progress"
        )
    
        # Classify each class name in a sequential loop
        for i, attr in enumerate(attributes):

            if isinstance(attr, (list, tuple)) and len(attr) >= 2:
                attr_name = str(attr[0]) if attr[0] is not None else "unknown"
                attr_type = str(attr[1]) if attr[1] is not None else "unknown"
            else:
                attr_name = str(attr)
                attr_type = "unknown"

            user_prompt = attribute_prompt(
                curr_attr=attr_name,
                curr_attr_type=attr_type,
                readme=readme,
                neighboring_classes=tokenized_neighbors,
                relevant_attrs=relevant_attrs,
                irrelevant_attrs=irrelevant_attrs,
                tokenized_name=curr_class
            )

            # Combine system + user to create final prompt
            input_prompt = llama_template.format(
                system_prompt=attr_classification_system_prompt,
                user_prompt=user_prompt
            )

            full_prompt = input_prompt
            
            # Encode the prompt
            input_ids = tokenizer.encode(
                input_prompt,
                encode_special_tokens=True,
                add_bos=False
            )        

            #generator.clear_queue()

            # Ensure it doesnt exceed max length
            if len(input_ids) > model_args.max_seq_len:
                print(f"Warning: Input prompt for '{attr}' exceeds max length ({len(input_ids)} > {model_args.max_seq_len})")
                input_ids = input_ids[:model_args.max_seq_len]

            # Create a new job
            job = ExLlamaV2DynamicJob(
                input_ids=input_ids,
                gen_settings=base_gen_settings,
                max_new_tokens=model_args.max_new_tokens,
                stop_conditions=[tokenizer.single_id("<|eot_id|>")],
                token_healing=True,
                identifier=i,  # Unique identifier for this job
            )

            generator.enqueue(job)  # Enqueue the job

            # Process this job immediately
            job_completed = False
            while not job_completed:
                results = generator.iterate()
                for result in results:
                    if result["eos"]:
                        response = result["full_completion"]
                        attr_name, classification_str = extract_attr_classification(response)
                        
                        if attr_name and classification_str:
                            if classification_str in ("relevant", "relevantattribute"):
                                relevant_attrs.append((attr_name, attr_type))
                                print(f"Classified '{attr_name}' as Relevant.")
                            elif classification_str in ("irrelevant", "non-relevant", "not relevant"):
                                irrelevant_attrs.append((attr_name, attr_type))
                                print(f"Classified '{attr_name}' as Irrelevant.")
                            
                            # rationales[attr_name] = rationale
                        else:
                            print(f"Warning: Failed to classify '{attr_name}'. Raw Response: {response}")
                        
                        job_completed = True
                        break

            # 3) After finishing classification for this attribute, update progress
            # return_data["rationales"][attr_name] = rationale
            progress.update(task_id, advance=1)
 
    # return_data["rationale"] = rationales

    # error bc json_data used to be passed as arg 
    return_data["classifications"] = {
        "Relevant": relevant_attrs,
        "Irrelevant": irrelevant_attrs,     # Keep track of the final (system+user) prompt template for reference
    }

    return_data["prompt_used"] = full_prompt

    print(f"Classified {len(relevant_attrs)} as Relevant and {len(irrelevant_attrs)} as Irrelevant for class {curr_class}")
    
    print(f"Attribute classification complete for class {curr_class}!")
    return return_data

def classify_methods(curr_class, methods, readme, model_args, tokenizer, generator):
    """
    Classify methods as relevant or irrelevant for a given class.
    Uses the ExLlamaV2 model and the supplied prompt templates.

    Args:
        curr_class (str): The name of the class being classified.
        tokenized_class_names (list): List of tokenized class names.
        methods (list): List of methods to classify.
        readme (str): The README content for context.
        relevant_methods (list): List of already classified relevant methods.
        irrelevant_methods (list): List of already classified irrelevant methods.
        model_args (ExLlamaArguments): Model configuration arguments.
        tokenizer (ExLlamaV2Tokenizer): Tokenizer instance.
        generator (ExLlamaV2DynamicGenerator): Generator instance.

    Returns:
        dict: Classification results with "Relevant" and "Irrelevant" methods.
    """
    
    relevant_methods = []
    irrelevant_methods = []

    # rationales = {}

    return_data = {
        "classifications":{},
        # "rationales": {},
        "prompt_used": ""
    }

    # generation settings used for all classifications
    base_gen_settings = ExLlamaV2Sampler.Settings(
        token_repetition_penalty=model_args.gen_settings[0],
        temperature=model_args.gen_settings[1],
    )

    full_prompt = ""

    method_names = methods.keys() if isinstance(methods, dict) else methods

    with get_basic_progress() as progress:
        print(curr_class)

        task_id = progress.add_task(
            "[green]Enqueuing methods...",
            total=len(methods),
            name="Queue adding Progress"
        )
    
        # Classify each class name in a sequential loop
        for  i, method in enumerate(method_names):
            user_prompt = method_prompt(
                curr_method=method,
                params = methods[method]["params"],
                return_type = methods[method]["return_type"],
                doc = methods[method]["doc"] if "doc" in methods[method] else "",
                readme=readme,
                relevant_methods=relevant_methods,
                irrelevant_methods=irrelevant_methods,
                tokenized_name=curr_class
            )

            # Combine system + user to create final prompt
            input_prompt = llama_template.format(
                system_prompt=method_classification_system_prompt,
                user_prompt=user_prompt
            )

            full_prompt = input_prompt
            
            # Encode the prompt
            input_ids = tokenizer.encode(
                input_prompt,
                encode_special_tokens=True,
                add_bos=False
            )        

            # Ensure it doesnt exceed max length
            if len(input_ids) > model_args.max_seq_len:
                print(f"Warning: Input prompt for '{method}' exceeds max length ({len(input_ids)} > {model_args.max_seq_len})")
                input_ids = input_ids[:model_args.max_seq_len]

            # Create a new job
            job = ExLlamaV2DynamicJob(
                input_ids=input_ids,
                gen_settings=base_gen_settings,
                max_new_tokens=model_args.max_new_tokens,
                stop_conditions=[tokenizer.single_id("<|eot_id|>")],
                token_healing=True,
                identifier=i,  # Unique identifier for this job
            )

            generator.enqueue(job)  # Enqueue the job

            # Process this job immediately
            job_completed = False
            while not job_completed:
                results = generator.iterate()
                for result in results:
                    if result["eos"]:
                        response = result["full_completion"]
                        method_name, classification_str = extract_method_classification(response)
                        
                        if method_name and classification_str:
                            if classification_str in ("relevant", "relevantmethod", "relevant method"):
                                relevant_methods.append(method_name)
                                print(f"Classified '{method_name}' as Relevant.")
                            elif classification_str in ("irrelevant", "non-relevant", "not relevant"):
                                irrelevant_methods.append(method_name)
                                print(f"Classified '{method_name}' as Irrelevant.")
                            
                            # rationales[method_name] = rationale
                        
                        job_completed = True
                        break
            
            # 3) After finishing classification for this attribute, update progress
            # return_data["rationales"][method_name] = rationale
            progress.update(task_id, advance=1)
 
    # return_data["rationale"] = rationales

    # error bc json_data used to be passed as arg 
    return_data["classifications"] = {
        "Relevant": relevant_methods,
        "Irrelevant": irrelevant_methods,     # Keep track of the final (system+user) prompt template for reference
    }

    print(f"Classified {len(relevant_methods)} as Relevant and {len(irrelevant_methods)} as Irrelevant for class {curr_class}")
    
    print(f"Method classification complete for class {curr_class}!")

    generator.clear_queue()  # Clear out the generator queue after processing all jobs
    return return_data

def add_associations(all_methods, curr_class, curr_attrs, possible_neighbors, neighbors_attrs, readme, model_args, tokenizer, generator):

    associations = []

    # rationales = {}

    return_data = {
        "associations":{},
        # "rationales": {},
        "prompt_used": ""
    }

    # generation settings used for all classifications
    base_gen_settings = ExLlamaV2Sampler.Settings(
        token_repetition_penalty=model_args.gen_settings[0],
        temperature=model_args.gen_settings[1],
    )

    with get_basic_progress() as progress:
        # The 'total' is how many classes we're going to classify.

        task_id = progress.add_task(
            "[green]Enqueuing neighbors...",
            total=len(possible_neighbors),
            name="Queue adding Progress"
        )
    
        # Classify each class name in a sequential loop
        for i, neighbor in enumerate(possible_neighbors):
            user_prompt = association_prompt(
                c1_class=curr_class,
                c1_attrs=curr_attrs,
                c1_methods=all_methods[curr_class] if curr_class in all_methods else [],
                c2_name=neighbor,
                c2_attrs=neighbors_attrs.get(neighbor, []),
                c2_methods=all_methods[neighbor] if neighbor in all_methods else [],
                readme=readme,
                curr_associations=associations,
            )

            # Combine system + user to create final prompt
            input_prompt = llama_template.format(
                system_prompt=method_classification_system_prompt,
                user_prompt=user_prompt
            )
            
            # Encode the prompt
            input_ids = tokenizer.encode(
                input_prompt,
                encode_special_tokens=True,
                add_bos=False
            )        

            generator.clear_queue()

            # Ensure it doesnt exceed max length
            if len(input_ids) > model_args.max_seq_len:
                print(f"Warning: Input prompt for '{neighbor}' exceeds max length ({len(input_ids)} > {model_args.max_seq_len})")
                input_ids = input_ids[:model_args.max_seq_len]

            # Create a new job
            job = ExLlamaV2DynamicJob(
                input_ids=input_ids,
                gen_settings=base_gen_settings,
                max_new_tokens=model_args.max_new_tokens,
                stop_conditions=[tokenizer.single_id("<|eot_id|>")],
                token_healing=True,
                identifier=i,  # Unique identifier for this job
            )

            generator.enqueue(job)  # Enqueue the job

            # Wait for generation to complete
            while generator.num_remaining_jobs():
                results = generator.iterate()
                for result in results:
                    if not result["eos"]:
                        continue  # Not done generating for this job

                    response = result["full_completion"]
                    # added print below for debugging
                    # print(f"Prompt:\n{input_prompt}\n\n ###======================== this is the response ===================###\n Response:\n{response}\n ###==================== end of response =============### ")
                    should_associate, association_type = extract_association_classification(response)
                    if should_associate is not None and association_type is not None:
                        if should_associate:
                            associations.append((neighbor, association_type))
                            print(f"Classified association between '{curr_class}' and '{neighbor}' as {association_type}.")
                        else:
                            print(f"Classified association between '{curr_class}' and '{neighbor}' as Not Associated.")
                    else:
                        print(f"'{curr_class}' and '{neighbor}' are not associated. Raw Response: {response}")

            # 3) After finishing classification for this attribute, update progress
            # return_data["rationales"][neighbor] = rationale

            # 3) After finishing classification for this attribute, update progress
            # return_data["rationales"][neighbor] = rationale
            progress.update(task_id, advance=1)
 
    # return_data["rationale"] = rationales

    return_data["associations"] = associations

    print(f"Added {len(associations)} associations for class {curr_class}")

    return return_data

# For testing / debugging 
if __name__ == "__main__":
    import sys
    import json

    # Check if correct number of arguments is passed
    if len(sys.argv) != 3:
        print("Usage: python xmiParser.py <path_to_xmi_file> <output_directory>")
        sys.exit(1)

    # Get the input XMI file and output directory from command line arguments
    xmi_file = sys.argv[1]
    output_dir = sys.argv[2]

    # Ensure the provided XMI file exists
    if not os.path.isfile(xmi_file):
        print(f"Error: The file {xmi_file} does not exist.")
        sys.exit(1)

    # Ensure the output directory exists, if not, create it
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except OSError as e:
            print(f"Error: Could not create output directory {output_dir}: {e}")
            sys.exit(1)

    # Extract class names
    try:
        class_names = xp.extract_class_names(xmi_file)
    except ValueError as e:
        print(e)
        sys.exit(1)

    # Remove duplicates
    unique_class_names = xp.remove_duplicates(class_names)

    # Define the output file path
    output_file = os.path.join(output_dir, 'class_names.json')

    # Save the unique class names to a JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump({"class_names": unique_class_names}, file, indent=4)
    except IOError as e:
        print(f"Error: Could not write to file {output_file}: {e}")
        sys.exit(1)

    # Print the count of unique class names
    print(f"Number of unique class names: {len(unique_class_names)}")
    print(f"Class names saved to {output_file}")

