print("Starting imports...")

import os
import traceback
import json
from itertools import combinations

print("Loading XML parser...")
import xmiParser

print("Loading utilities...")
import time
import tokenizer
import sbertEmbeddings
import cleanXML as cleanXML
import sys

print("Loading transformer models...")
from transformers import HfArgumentParser
from config import ExLlamaArguments

print("Loading inference and metrics modules...")
from inference import LLMClassifier
import metrics
import umpParser

from compute_associations import get_bridging_associations
import sys

# TODO : add cardinalities to inference and perhaps more restrictions 

print("All imports complete!\n")

def create_json(xml_file, readme_file, tokenization=True, similarity_ranking=True):
    """
    Create an internal JSON structure to store data throughout the workflow.
    """
    # Step 1: Extract raw class names from the xml file
    print("Extracting class names from xml...")
    class_names = xmiParser.extract_class_names(xml_file)
    print(class_names) # debug
    unique_class_names = xmiParser.remove_duplicates(class_names)
    print(unique_class_names) # debug

    print("Class names extracted and duplicates removed.")

    # Step 2: Tokenize class names
    print("Tokenizing class names...")
    if tokenization:
        tokenized_class_names = tokenizer.tokenize_class_names(unique_class_names)
        print("Class names tokenized.")
    else:
        tokenized_class_names = unique_class_names # for simplicity keep the name of the key 

        print("Skipping tokenization, using original class names as tokenized names.")

    # Similarly, add class ids from the xml file 
    class_id_map = xmiParser.extract_class_ids(xml_file, class_names)

    print("Class IDs extracted:", class_id_map) # debug  
    # unique_class_ids = xmiParser.remove_duplicates(class_ids)

    # Step 3: Read README content
    print("Reading README file...")
    if not os.path.exists(readme_file):
        print("README file does not exist.")
        readme_content = ""
    else:
        with open(readme_file, "r", encoding="utf-8") as f:
            readme_content = f.read()

    # Initialize JSON structure
    data = {
        "raw_class_names": unique_class_names,
        "class_ids": class_id_map,
        "readme": readme_content,
        "tokenized_class_names": tokenized_class_names, # for now if no tokenization theyre the regular class names 
        "ranked_classes": [],
        "classifications": [],
        "prompt_used": None
    }
    print("JSON structure created.")
    return data

def load_json(json_file):
    """Load the JSON data from the specified file."""
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

def map_tokenized_to_original(json_data, tokenized_class_names):
    """
    Map tokenized class names back to their original names.
    """
    original_class_names = []
    for tokenized_name in tokenized_class_names:
        for original_name, tokenized in json_data["tokenized_class_names"].items():
            if tokenized == tokenized_name:
                original_class_names.append(original_name)
    return original_class_names

def get_class_pairs(all_class_names, all_class_neighbors):
    """
    Return all the class pairs that our current class is NOT neighboring with.
    In order to check if we can create an association between them, since there 
    already isnt one in the class diagram. 

    Returns: 
    {
    'ClassA': ['ClassB', 'ClassC', 'ClassD'],  # ClassA has no associations with B, C, or D
    'ClassB': ['ClassC', 'ClassE'],            
    'ClassC': ['ClassE'],                      
    }
    """
    class_pairs_map = {}

    for class1, class2 in combinations(all_class_names, 2):
        # Check if there's no existing association between the classes
        has_association = (
            class2 in all_class_neighbors[class1].get("Association", []) or
            class1 in all_class_neighbors[class2].get("Association", [])
        )
        # has_generalization = (
        #     class2 in all_class_neighbors[class1].get("Generalization", []) or
        #     class1 in all_class_neighbors[class2].get("Generalization", [])
        # )
        if not has_association:
            class_pairs_map.setdefault(class1, []).append(class2)
    
    return class_pairs_map

def id_to_name_mapping(json_data):
    """Create a mapping from class IDs to original class names."""
    return {v: k for k, v in json_data["class_ids"].items()}
# -----------------------------------------------------------
# 2) MAIN WORKFLOW
#    - Load ExLlama once
#    - Create + rank JSON
#    - Classify with loaded model
#    - Save JSON
#    - Remove Implementation classes
# -----------------------------------------------------------

def main(xml_file, readme_file, model_args, labels_file, results_file, iteration=0, tokenization=True, similarity_ranking=True, readme=None):
    """
    Main workflow to process XMI and README files.
    """

    project_name = os.path.basename(os.path.dirname(xml_file))

    # Step 1: Create initial JSON structure (with initial class names & ids)
    print("Creating initial JSON structure...")
    init_data = create_json(xml_file, readme_file, tokenization=tokenization, similarity_ranking=similarity_ranking)

    # Load your ExLlamaV2 model ONCE here (instead of in classify_classes)
    print("Loading ExLlama model + tokenizer + generator once...")
    # INITIALIZE INFERENCE HERE 
    inference = LLMClassifier(model_args, init_data["readme"])

    print("Model loaded successfully.")

    # Step 2: Use SBERT to rank class names
    print("Ranking class names using SBERT...")

    if similarity_ranking:
        data = sbertEmbeddings.calculate_similarity_and_rank(init_data)
        print("Class names ranked successfully.")
    else:
        data = init_data
        print("Skipping similarity ranking, using original class names order.")

    #data = sbertEmbeddings.calculate_similarity_and_rank(init_data)
    #print("Class names ranked successfully.")

    # metrics_object to compute precision over all class classifications, attributes and methods 
    metrics_object = {}

    ###### CLASSES ######

    # Step 3: Use LLM to classify ranked class names (pass the loaded model objects)
    print("Classifying class names using LLM...")

    # data = inference.batch_classify_classes(data, model_args, tokenizer, generator)
    # data = inference.classify_classes(data, model_args, tokenizer, generator)

    # # Step 4: Save final JSON file
    # xmi_base = os.path.splitext(os.path.basename(xml_file))[0]
    # output_json_file = f"./{xmi_base}_output.json"

    # with open(output_json_file, "w", encoding="utf-8") as f:
    #     json.dump(data, f, indent=4)
    # print(f"First JSON saved to {output_json_file}")

    # print("Re-classifying high-confidence domain-specific classes...")

    # # Filter domain-specific classes by confidence score
    # high_confidence_domain_classes = []
    # confidence_scores = data["classifications"].get("Confidence Scores", {})

    # for class_name in data["classifications"]["Domain-specific"]:
    #     confidence = confidence_scores.get(class_name)
    #     if confidence is not None and confidence >= 0.9:
    #         high_confidence_domain_classes.append(class_name)
    #         print(f"Including '{class_name}' (confidence: {confidence})")
    #     else:
    #         print(f"Excluding '{class_name}' (confidence: {confidence})")

    # print(f"Filtered from {len(data['classifications']['Domain-specific'])} to {len(high_confidence_domain_classes)} high-confidence classes")

    # domain_specific_data = dict(init_data)
    # domain_specific_data["tokenized_class_names"] = high_confidence_domain_classes  # Use filtered list
    # domain_specific_data["ranked_classes"] = high_confidence_domain_classes  # Use filtered list
    # domain_specific_data["classifications"] = {} 

    # For debug purposes
    # print(domain_specific_data)

    # input("Press Enter to continue with re-classification...")
    
    # Reclassify but this time without the uncertainty 
    #reclassified_data = inference.reclassify_classes(domain_specific_data, model_args, tokenizer, generator)

    reclassified_data = inference.classify_classes(json_data = data, similarity_ranking=similarity_ranking)

    all_class_names = xmiParser.extract_class_names(xml_file) # all the class names for ALL the classes

    # print('ALL CLASS NAMES:', all_class_names)

    print("CLASS IDS", data["class_ids"])

    all_class_neighbors = {}

    ids = id_to_name_mapping(data)
    for c in all_class_names:
        neighbors = xmiParser.extract_class_neighbors(xml_file, c)

        all_class_neighbors[c] = neighbors

        # Map neighbor IDs to their original class names
        if neighbors:
            for rel_type in neighbors:
                neighbors[rel_type] = [ids.get(neighbor_id, neighbor_id) for neighbor_id in neighbors[rel_type]]
        
        print(c, neighbors)
    
    print("All class neighbors extracted:")
    for class_name, neighbors in all_class_neighbors.items():
        print(f"  {class_name}: {neighbors}")


    xmi_base = os.path.splitext(os.path.basename(xml_file))[0]
    output_json_file_2 = f"../model_outputs/{project_name}_classes_result.json"

    with open(output_json_file_2, "w", encoding="utf-8") as f:
        json.dump(reclassified_data, f, indent=4)
    print(f"Second JSON saved to {output_json_file_2}")

    # Step 6.1: Load JSON and extract implementation details
    print("Extracting implementation detail classes...")
    implementation_details = (
        data["classifications"].get("Implementation detail", []) +
        reclassified_data["classifications"].get("Implementation detail", [])
    ) # they're already tokenized 

    json_data = load_json(output_json_file_2) # unnecessary loading? 

    # Step 6.2: Map tokenized names back to original class names
    print("Mapping tokenized class names to original class names...")
    implementation_details_original_names = map_tokenized_to_original(data, implementation_details)

        # Get all the associations the domain model should have without impl classes, but before inference (so transitive)
    bridging_associations = get_bridging_associations(all_class_neighbors, implementation_details_original_names)

    print("Bridging associations to add:", bridging_associations)


        # pause for debugging before removing impl classes and adding associations
    # input("Check the bridging associations before continuing...")

    # Step 6.3 : Remove implementation detail classes from XML
    print("Removing implementation detail classes from XML...")
    class_xml_path = cleanXML.remove_implementation_classes(xml_file, implementation_details_original_names)
    print("Implementation detail classes removed successfully.")
	

     # Remove irrelevant classes from neighbors
    for impl_class in implementation_details_original_names:
        if impl_class in all_class_neighbors:
            del all_class_neighbors[impl_class]
        if impl_class in all_class_names:
            all_class_names.remove(impl_class)
    # Step 6.4 : Update the XML/JSON we're working with 
    #json_data = create_json(class_xml_path, readme_file) # comment bc of unnecessary loading

    ###### METHODS ######

    # Step 8: Remove irrelevant methods 

    # Setup (model_method_results.json, project_output2.json)
    model_output_file = f"../model_outputs/{project_name}_method_results.json"
    with open(model_output_file, "w", encoding="utf-8") as f:
        pass # clear the file 

    methods_xml_path = class_xml_path.replace("modified_1", "modified_2") # build upon the previous xml file with attributes removed
    with open(class_xml_path, "r", encoding="utf-8") as src, open(methods_xml_path, "w", encoding="utf-8") as dst:
        dst.write(src.read())

    # print("methods output path", methods_xml_path)

    all_class_names = xmiParser.extract_class_names(methods_xml_path) # all the class names for ALL the classes

    method_classifications = {}

    # First remove constructors and getters/setters from each class' methods and write that to methods_xml_path 
    curr_xml = class_xml_path

    for c in all_class_names:
        print("Current class: ", c)

        print("Removing constructors from classes")
        cleanXML.remove_constructor(curr_xml, methods_xml_path, c)

        curr_xml = methods_xml_path

        print("Removing getters & setters...")
        cleanXML.remove_getters_setters(curr_xml, methods_xml_path, c)
        
    # input("Check file before continuing!! ...")

    all_methods = {}

    # Time to classify hihi
    # for c in all_class_names: 
    #     # Get all the remaining methods of the class 
    print("Extracting methods for class:", c)
    methods = xmiParser.extract_class_methods(methods_xml_path, c)

    #     all_methods[c] = methods

    #     print("Classifying methods for class:", c)

    #     # TODO: tokenize method names? 

    #     # params & return type 
        
    #     data = inference.classify_methods(c, methods)

    #     method_classifications[c] = {
    #         "classifications": data["classifications"]
    #         # "rationales": data.get("rationales", {})
    #     }

    #     # now in cleanXML, remove those methods from the diagram & put it in a new file
    #     cleanXML.remove_irrelevant_methods(data["classifications"]["Irrelevant"], c, methods_xml_path)

    # Pause to check if the methods were removed     
    # input("Check file before continuing!!! ...")
    
    # JSON file for tracing output 
    with open(model_output_file, "a", encoding="utf-8") as f:
        json.dump(method_classifications, f, indent=4)

    for c in all_class_names:
        metrics_object[c] = {
            "Attributes": [],
            "Methods" : [],
        }

    print(metrics_object) # double check 

    ###### ATTRIBUTES ######

    # Step 7: Clean up the attributes for each domain-specific class 
    
    # Step 7.1: Now that we have the cleaned XML with only domain-specific classes, get the attributes for each class and put that in a dictionary
    print("Extracting class attributes...")
    all_class_attrs = xmiParser.extract_class_attributes(class_xml_path) # all the attributes for ALL the classes 

    print(all_class_attrs)

    all_class_names = all_class_attrs.keys() # could also be done with xmiParser.extract_class_names(class_xml_path)

    # Step 7.2: Now extract the neighboring classes of each class, like a graph 
    print("Getting class neighbors...")

    class_ids = json_data["class_ids"] # delete? 
    id_to_name = {v: k for k, v in class_ids.items()}

    # For debugging 
    print("id_to_name:", id_to_name)

    # Step 7.3: For each of those classes, classify which of its attributes is relevant or not
    print("Classifying attributes for each class...")
    attr_classification = {}

    attr_xml_path = methods_xml_path.replace("modified_2", "modified_3")

    print("attr_xml_path", attr_xml_path)

    # Copy contents from class_xml_path to attr_xml_path
    with open(methods_xml_path, "r", encoding="utf-8") as src, open(attr_xml_path, "w", encoding="utf-8") as dst:
        dst.write(src.read())

    model_output_file = f"../model_outputs/{project_name}_attr_results.json"
    with open(model_output_file, "w", encoding="utf-8") as f:
        pass # clear the file 

    for c in all_class_names:        
        print("Current class: ", c)
        print(all_class_attrs[c])

        if all_class_attrs[c] == []:
            continue

        data = inference.classify_attributes(
            curr_class=c,
            tokenized_class_names=json_data['tokenized_class_names'],
            attributes=all_class_attrs[c],
            neighboring_classes=all_class_neighbors[c]
        )

        # Store the classification results for each class
        attr_classification[c] = {
            "class_name": c,
            "classifications": data["classifications"]
            # "rationales": data.get("rationales", {})
        }

        attr_classification[c] = data["classifications"] # store in a variable why? 

        cleanXML.remove_irrelevant_attrs(data["classifications"]["Irrelevant"], c, attr_xml_path)

    # input("Check file before continuing!!!! ...")

    with open(model_output_file, "a", encoding="utf-8") as f:
        json.dump(attr_classification, f, indent=4)

    for c in attr_classification.keys():
        metrics_object[c]["Attributes"] = [a[0] for a in attr_classification[c]["Relevant"]]

    print(metrics_object)

    #input("METRICS OBJECT?! ...") # double check + pause the code here for debugging    

    ###### ASSOCIATIONS / RELATIONSHIPS ######

    # Step 9: Add any missing logical associations between classes
    print("Beginning associations between classes...")

    model_output_file = f"../model_outputs/{project_name}_association_results.json"
    with open(model_output_file, "w", encoding="utf-8") as f:
        pass 

    assos_xml_path = attr_xml_path.replace("modified_3", "modified_4") # build upon the previous xml file with attributes removed
    with open(attr_xml_path, "r", encoding="utf-8") as src, open(assos_xml_path, "w", encoding="utf-8") as dst:
        dst.write(src.read())

    print("assos_xml_path", assos_xml_path)

    class_pairs_map = get_class_pairs(all_class_names, all_class_neighbors)
    for c1 in list(class_pairs_map.keys()):
        class_pairs_map[c1] = [
            c2 for c2 in class_pairs_map[c1]
            if tuple(sorted([c1, c2])) not in bridging_associations
        ]
        if not class_pairs_map[c1]:
            del class_pairs_map[c1]

    print("Class pairs map (after excluding bridging pairs):", class_pairs_map)

    # Reextract attributes after removing irrelevant ones
    all_class_attrs = xmiParser.extract_class_attributes(attr_xml_path)

    # Only ask the LLM about pairs with no existing association
    # class_pairs_map = get_class_pairs(all_class_names, all_class_neighbors)

    inferred_pairs = set()

    for c1, candidates in class_pairs_map.items():
        neighbors_attrs = {c2: all_class_attrs.get(c2, []) for c2 in candidates}

        data = inference.add_associations(
            all_methods=all_methods,
            curr_class=c1,
            curr_attrs=all_class_attrs.get(c1, []),
            possible_neighbors=candidates,
            neighbors_attrs=neighbors_attrs,
        )

        for c2_name, association_type in data["associations"]:
            inferred_pairs.add(tuple(sorted([c1, c2_name])))
    
    # Merge bridged + inferred associations (both are sets of sorted tuples)
    all_associations = bridging_associations | inferred_pairs

    final_metrics_object = {
        "classes": metrics_object,
        "associations": [list(pair) for pair in sorted(all_associations)],
    }

    # Collect all associations (pre-existing + newly added) for metrics
    # final_metrics_object = {"classes": metrics_object, "associations": []}
    # seen_pairs = set()

    # for c in all_class_names:
    #     for assoc in xmiParser.extract_class_neighbors(assos_xml_path, c).get("Association", []):
    #         pair = tuple(sorted([c, id_to_name[assoc]]))
    #         if pair not in seen_pairs:
    #             seen_pairs.add(pair)
    #             final_metrics_object["associations"].append(list(pair))

    # Add EVERY association in the final XML to the metrics object 
    # final_metrics_object = {
    #     "classes": metrics_object,
    #     "associations": []
    # }

    # # By extracting all the current associations from the XML 
    # curr_assos = []

    # for c in all_class_names:
    #     neighbors = xmiParser.extract_class_neighbors(assos_xml_path, c)
    #     if "Association" in neighbors:
    #         for assoc in neighbors["Association"]:
    #             pair = tuple(sorted([c, id_to_name[assoc]]))
    #             if pair not in curr_assos:
    #                 curr_assos.append(pair) # TODO: review this 
    #                 final_metrics_object["associations"].append(list(pair))

    # Time to validate!! 

    # Output metrics_object to a file (json)
    metrics_output_file = os.path.join(
        os.path.dirname(labels_file) if labels_file else "./model_outputs",
        f"final_metrics_iter{iteration}.json"
    )
    with open(metrics_output_file, "w", encoding="utf-8") as f:
        json.dump(final_metrics_object, f, indent=4)
    print(f"Metrics saved to {metrics_output_file}")

    print("Final metrics object: ", final_metrics_object)

    # if labels_file is None:
    #     print("WARNING: No labels file found - skipping metrics comparison")
    # elif labels_file.endswith(".json"):
    #     with open(labels_file, "r", encoding="utf-8") as f:
    #         labels_dict = json.load(f)
    #         metrics.compare(
    #             labels=labels_dict,
    #             output=final_metrics_object,
    #             results_file=results_file, 
    #             iter_no=iteration
    #         )   
    # elif labels_file.endswith(".ump"):
    #     print(f"Running metrics comparison with .ump file: {labels_file}")
    #     metrics.compare_ump(
    #         gt=umpParser.main(labels_file), # ground truth in json format 
    #         output=final_metrics_object,
    #         results_file=results_file, 
    #         iter_no=iteration
    #     )
    # else:
    #     print(f"WARNING: Unknown labels file format: {labels_file}")

def run_all_projects(model_args, max_projects=0, iterations=0, tokenization=True, similarity_ranking=True, readme=None):
    base_dir = "../data_mcgill"
    projects = sorted(os.listdir(base_dir))

    print(f"running projects in {base_dir}: {projects}")

    # Optionally limit how many projects to run
    if max_projects != 0 and max_projects < len(projects):
        projects = projects[:max_projects+1]
        print(f"Limiting to first {max_projects} projects: {projects}")
    else:
        projects = projects
        print(f"Running all {len(projects)} projects: {projects}")

    if iterations > 0:
        for i in range(iterations):
            print(f"\nRunning iteration {i+1} of {iterations} for all projects...")

            for project in projects:
                project_path = os.path.join(base_dir, project)

                if not os.path.isdir(project_path):
                    continue

                print("\n===================================")
                print(f"Running project: {project}, iter {i+1}")
                print("===================================\n")

                xml_file = os.path.join(project_path, "project.xml")
                readme_file = os.path.join(project_path, "readme.md")

                # optional files
                labels_file = next((os.path.join(project_path, f) for f in os.listdir(project_path) if f.endswith(".ump")), None)
                results_file = os.path.join(project_path, "results.csv")
                # CSV file will be created by metrics.py with headers when first written to

                ump_output = umpParser.main(labels_file)
                ump_output_file = os.path.join(project_path, "ump_parsed.json")
                with open(ump_output_file, "w", encoding="utf-8") as f:
                    json.dump(ump_output, f, indent=4)

                if labels_file:
                    print(f"Found labels file: {labels_file}")
                else:
                    print(f"WARNING: No .ump labels file found for {project}")

                if not os.path.exists(xml_file):
                    print(f"Skipping {project} (no project.xml)")
                    continue

                try:
                    main(
                        xml_file=xml_file,
                        readme_file=readme_file,
                        model_args=model_args,
                        labels_file=labels_file,
                        results_file=results_file,
                        iteration=i,
                        tokenization=tokenization,
                        similarity_ranking=similarity_ranking,
                        readme=readme
                    )
                except Exception as e:
                    print(f"Error running {project}: {e}")
                    traceback.print_exc()
    

def fetch_sources() :
    with open('/u/mancasat/Desktop/summer_intern/domain-concepts-identification-using-LLMs-aless/src/sources.json', 'r') as file:
        data = json.load(file)

    for i in range(len(data)):
        print(i, data[i]["name"])

    source = input("Which source project would you like to work with? ")

    # Returns class diagram xml, readme file, csv to enter metrics, labels file 
    return data[int(source)]["class-diagram"], data[int(source)]["readme"], data[int(source)]["csv"], data[int(source)]["labels"]

if __name__ == "__main__":
    from transformers import HfArgumentParser

    parser = HfArgumentParser(ExLlamaArguments)
    model_args = parser.parse_args_into_dataclasses()[0]

    run_all_projects(
        model_args,
        model_args.max_projects,
        1, # iterations
        model_args.tokenization,
        model_args.similarity_ranking,
        model_args.readme
    )


# -----------------------------------------------------------

# ALESS NOTES
# xml/xml file is the class diagram that we reverse-engineered from the source code of a project
# format for the xml should be a regular path string same for the readme

