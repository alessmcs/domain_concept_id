import xml.etree.ElementTree as ET
import os

# ANY XMI IS ACTUALLY XML!

def create_metrics_dict(xml_file):
    """
    Create a dictionary matching the structure of labels.json from the given xml file.

    
    Args:
        xml_file (str): Path to the xml file.

    Returns:
        dict: A dictionary where keys are class names and values are lists of attributes.
    """

    final_dict = {}
    class_attributes = extract_class_attributes(xml_file)

    for name in class_attributes.keys():
        final_dict[name] = {
            "Attributes" : class_attributes[name],
            "Methods" : extract_class_methods(xml_file, name),
        }

    return final_dict



def extract_class_attributes(xml_file):
    """
    Extract class attributes from an xml file.

    Args:
        xml_file (str): Path to the xml file.

    Returns:
        dict: A dictionary where keys are class names and values are lists of tuples (attr_name, attr_type).
    """
    # Parse the xml file
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Error parsing the xml file: {e}")

    class_attributes = {}

    # Find all 'Class' elements in the xml file
    for class_element in root.findall(".//Class"):
        class_name = class_element.get("Name")
        if class_name is None:
            continue  # Skip if class name is not found

        attributes = []
        model_children = class_element.find(".//ModelChildren")
        if model_children is None: continue
        for attribute_element in model_children.findall(".//Attribute"):
            attr_name = attribute_element.get("Name")
            attr_type = attribute_element.get("Type")
            if attr_name:
                attributes.append((attr_name, attr_type))

        class_attributes[class_name] = attributes

    return class_attributes

def extract_class_methods(xml_file, class_name):
    """
    Extract class methods from an xml file for a specific class.

    Args:
        xml_file (str): Path to the xml file.
        class_name (str): Name of the class to extract methods from.

    Returns:
        methods: A dict such that:
            {"method_name" : {
                "params" : [ (param_name, param_type, doc), ... ],
                "return_type" : return_type,
                "doc" : documentation_plain (if available)
            }
            ...}
    """
    # Parse the xml file
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Error parsing the xml file: {e}")

    methods = {}

    # Find the specific class element
    class_element = root.find(f".//Class[@Name='{class_name}']")
    if class_element is None:
        return methods  # Return empty list if class not found
    
    # Find all 'Operation' elements within the class
    model_children = class_element.find(".//ModelChildren")
    if model_children is None:
        return methods
    
    for m in model_children.findall(".//Operation"):
        method_name = m.get("Name")
        method_params = []
        return_type = m.get("ReturnType")
        method_doc = m.get("Documentation_plain")

        for param in m.findall(".//Parameter"):
            param_name = param.get("Name")
            param_type = param.get("Type")
            param_doc = param.get("Documentation_plain")
            if param_doc is not None and len(param_doc) > 0: 
                method_params.append((param_name, param_type, param_doc))
            else: 
                method_params.append((param_name, param_type)) # some methods may not have documentation but it's useful info if it's present 

        if method_name:
            if method_doc is not None and len(method_doc) > 0:
                methods[method_name] = {
                    "params": method_params,
                    "return_type": return_type,
                    "doc": method_doc
                }
            else:
                methods[method_name] = {
                    "params": method_params,
                    "return_type": return_type
                }

    return methods 

# TODO: review this entire function 
def extract_class_neighbors(xml_file, curr_class_name):
    print("extracting neighbors for class: ", curr_class_name)
    # Given a class and its existing associations (in the class diagram), get the class names of its direct neighbors 

    # TODO REMOVE THIS PART AND INCLUDE IT IN CLEANXML !!!!!
    # If a class isnt an implementation class, dont include it in neighbors 
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # print(root.tag)
    class_map = {}

    for clazz in root.findall(".//Class"):
        class_id = clazz.get("Id")
        if class_id is not None:
            class_map[class_id] = clazz

    neighbors = {
        "Generalization" : [],
        "Association" : []
    }
    # TODO: other kinds of relationships!! (Realization)
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Error parsing the xml file: {e}")
    
    ids = extract_class_ids(xml_file, curr_class_name)
    
    # Get the class' id (TODO: remove???)
    class_element = root.find(f".//Class[@Name='{curr_class_name}']")
    if class_element is None: 
        return neighbors

    class_id = class_element.get("Id")
    if class_id is None:
        return neighbors
    
    # Will return a list of <ModelRelationshipContainer>s, each belonging to a type of association 
    container = root.find(".//ModelRelationshipContainer")
    if container is None: 
        return neighbors
    
    all_relationships = container.find(".//ModelChildren") 
    if all_relationships is None:
        return neighbors
    
    #print([c.get("Name") for c in all_relationships]) # debug print

    for elem in all_relationships:
        rel_type = elem.get('Name')
        if rel_type == "Generalization":
            all_generalizations = elem.findall(".//Generalization")
            for r in all_generalizations: 
                # <Generalization ... From = [current] ... Id = [what we want] ..>
                if r.get('From') == class_id :
                    voisin_id = r.get("To")
                    if voisin_id in class_map.keys():
                        neighbors["Generalization"].append(class_map[voisin_id].get("Name"))
                else: continue
        elif rel_type == "Association":
            all_associations = elem.findall(".//Association")
            for r in all_associations:
                # Get FromEnd/AssociationEnd/Qualifier.Id
                from_qualifier = r.find(".//FromEnd/AssociationEnd")
                if from_qualifier is None:
                    continue

                from_id = from_qualifier.get("EndModelElement")
                print(class_id)
                print(from_id)
                if from_id != class_id:
                    continue

                # Get ToEnd/AssociationEnd/Type/Class.Name
                to_class = r.find(".//ToEnd/AssociationEnd/Type/Class")
                if to_class is not None:
                    class_name = to_class.get("Name")
                    class_id = to_class.get("Idref")
                    print(class_name)
                    if class_name and class_id in class_map.keys():
                        neighbors["Association"].append(class_id)
        
    print("neighbors ", neighbors)
    return neighbors


def extract_class_names(xml_file):
    """
    Extract class names from an xml file.

    Args:
        xml_file (str): Path to the xml file.

    Returns:
        list: A list of class names extracted from the xml file.
    """
    # Parse the xml file
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Error parsing the {xml_file}: {e}")

    class_names = []

    # Find all 'Class' elements in the xml file and extract their 'Name' attribute
    for class_element in root.findall(".//Class"):
        class_name = class_element.get("Name")
        if not class_name:
            continue
            
        # Skip if we already have this class name
        if class_name in class_names:
            continue
            
        # Method 1: Check if it has ModelChildren (indicates actual class definition)
        model_children = class_element.find("ModelChildren")
        if model_children is not None:
            class_names.append(class_name)
            continue

    return class_names 

def extract_class_ids(xml_file, class_names):
    """
    Extract class IDs from an xml file.

    Args:
        xml_file (str): Path to the xml file.

    Returns:
        dict: A dictionary where keys are class names and values are their IDs.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Error parsing the xml file: {e}")

    class_id_map = {}

    # Search for each class directly without going through packages
    # if class names is a string, convert it to a list
    if isinstance(class_names, str):
        class_names = [class_names]
        
    for class_name in class_names:
        # Find all Class elements with this name 
        class_elements = root.findall(f".//Class[@Name='{class_name}']")
        
        if class_elements:
            # Look for the actual class element, not just a graphical representation
            for element in class_elements:
                # Check if this is a real class definition by looking for ModelChildren
                if element.find(".//ModelChildren") is not None:
                    class_id_map[class_name] = element.get("Id")
                    break
            
            # If no class definition found, use first occurrence
            if class_name not in class_id_map:
                class_id_map[class_name] = class_elements[0].get("Id")
        else:
            class_id_map[class_name] = None

    return class_id_map

def remove_duplicates(class_names):
    """
    Remove duplicate class names from the list.

    Args:
        class_names (list): A list of class names.

    Returns:
        list: A list of unique class names.
    """
    return list(dict.fromkeys(class_names))


if __name__ == "__main__":
    import sys
    import json 

    # DELETE!
    files = "/u/mancasat/Desktop/summer_intern/domain-concepts-identification-using-LLMs-aless/data/Hotel-Management/project_modified.xml"
    print(extract_class_names(files))


    ### TO TEST EXTRACT_CLASS_NEIGHBORS & EXTRACT_CLASS_ATTRIBUTES
    test_xml_file = "/u/mancasat/Desktop/summer_intern/domain-concepts-identification-using-LLMs-aless/data/Espresso/project_modified.xml"

    # attributes = extract_class_attributes(test_xml_file)
    # print(f"Extracted attributes: {attributes}")

    # for c in attributes.keys():
    #     voisins = extract_class_neighbors(test_xml_file, c)
    #     print(voisins)

    # # Check if correct number of arguments is passed
    # if len(sys.argv) != 3:
    #     print("Usage: python xmlParser.py <path_to_xml_file> <output_directory>")
    #     sys.exit(1)
 
    # # Get the input xml file and output directory from command line arguments
    # xml_file = sys.argv[1]
    # output_dir = sys.argv[2]

    # # Ensure the provided xml file exists
    # if not os.path.isfile(xml_file):
    #     print(f"Error: The file {xml_file} does not exist.")
    #     sys.exit(1)

    # # Ensure the output directory exists, if not, create it
    # if not os.path.exists(output_dir):
    #     try:
    #         os.makedirs(output_dir)
    #     except OSError as e:
    #         print(f"Error: Could not create output directory {output_dir}: {e}")
    #         sys.exit(1)

    # # Extract class names
    # try:
    #     class_names = extract_class_names(xml_file)
    # except ValueError as e:
    #     print(e)
    #     sys.exit(1)

    # # Remove duplicates
    # unique_class_names = remove_duplicates(class_names)

    # # Define the output file path
    # output_file = os.path.join(output_dir, 'class_names.json')

    # # Save the unique class names to a JSON file
    # try:
    #     with open(output_file, 'w', encoding='utf-8') as file:
    #         json.dump({"class_names": unique_class_names}, file, indent=4)
    # except IOError as e:
    #     print(f"Error: Could not write to file {output_file}: {e}")
    #     sys.exit(1)

    # # Print the count of unique class names
    # print(f"Number of unique class names: {len(unique_class_names)}")
    # print(f"Class names saved to {output_file}")
