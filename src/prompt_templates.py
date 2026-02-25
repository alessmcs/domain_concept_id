llama_template = (
    "<|start_header_id|>system<|end_header_id|>\n\n"
    "{system_prompt}<|eot_id|>"
    "<|start_header_id|>user<|end_header_id|>\n\n"
    "{user_prompt}<|eot_id|>"
    "<|start_header_id|>assistant<|end_header_id|>\n\n"
)

method_classification_system_prompt = """You are an expert in classifying methods into relevant or irrelevant for the given entity."""
review_classification_system_prompt = """You are an expert in classifying objects into domain-specific or implementation details."""
attr_classification_system_prompt = """You are an expert in classifying attributes into relevant or irrelevant for the given class."""
association_classification_system_prompt = """You are an expert in inferring associations between classes based on software engineering principles."""

# Prompt for method classification 
def method_prompt(curr_method, params, return_type, doc, readme, relevant_methods, irrelevant_methods, tokenized_name):
    
    # Format parameters as a string
    # p: param, t: type of parameter, d: description
    params_str = ', '.join(
        f"{p}: {t} ({d})" if len(param) == 3 else f"{p}: {t}"
        for param in params
        for p, t, *rest in [param]
        for d in (rest[0] if rest else '')
    ) if params else 'None'

    readme_section = f"### readMe:\n{readme}\n\n" if readme else ""
    
    method_classification_template = f"""
                ### Instruction:
                # Strictly classify whether the given method is relevant or irrelevant for the given entity, represented as a class.
                # A relevant method is strictly one that describes the entity's behavior. 
                # Heavily consider the TYPE of the software described in the following readMe and its architecture.

                # MUST keep the response concise ONLY limited to the output format.

                ### Examples:
                - Health management system:
                + Relevant: 'getPatientDetails', 'scheduleAppointment', 'generateLabReport', 'prescribeMedication'
                + Irrelevant: 'debugMethod', 'temporaryStorageHandler', 'logErrorDetails'

                {readme_section}

                ### Current classifications:
                - Current class: '{tokenized_name}'
                - Relevant: {', '.join(relevant_methods) if relevant_methods else 'None'}
                - Irrelevant: {', '.join(irrelevant_methods) if irrelevant_methods else 'None'}
                
                ### given class: '{tokenized_name}'
                ### given method: '{curr_method}'
                ### parameters: {params_str}
                ### return type: {return_type if return_type else 'void'}
                ### docstring: {doc if doc else 'None'}

                ### Example of output:
                {{
                "method": [given method],
                "classification": "Relevant"
                }}

    """

    return method_classification_template

# Prompt for attribute classification
def attribute_prompt(curr_attr, curr_attr_type, readme, neighboring_classes, relevant_attrs, irrelevant_attrs, tokenized_name):

    # Format neighboring classes as a string preserving the relationship types
    neighbor_str = (
        ', '.join(
            f"{rel_type}: [{', '.join(names) if names else 'None'}]"
            for rel_type, names in neighboring_classes.items() 
        ) if neighboring_classes else 'None'
    )

    print(neighbor_str)

    def format_attrs(attrs):
        return ', '.join([f"{name} ({type_})" for name, type_ in attrs]) if attrs else 'None'

    attribute_classification_template = f"""
                ### Instruction:
                # Strictly classify whether the given attribute is relevant or irrelevant for the given class.
                # Heavily consider the TYPE of the software described in the following readMe and its architecture.
                # Consider the attribute's type, its class name and its immediate neighboring classes to determine the relevance of the attribute. 

                # MUST keep the response concise ONLY limited to the output format.

                ### Examples:
                - Health management system:
                + Relevant: 'patientName', 'appointmentDate', 'doctorId', 'labReportId', 'prescriptionId'
                + Irrelevant: 'readable', 'debugFlag', 'temporaryStorage', 'employees', 'employeeInfo',   

                ### readMe:
                {readme}

                ### Current classifications:
                - Current class: '{tokenized_name}'
                - Relevant: {format_attrs(relevant_attrs)}
                - Irrelevant: {format_attrs(irrelevant_attrs)}
                - Neighboring classes: {neighbor_str}
                
                ### given class: '{tokenized_name}'
                ### given attribute: '{curr_attr}'
                ### given attribute type: '{curr_attr_type}'

                ### Example of output:
                {{
                "attribute": "{curr_attr}",
                "classification": "Relevant" or "Irrelevant"
                }}

    """

    if(neighbor_str != 'None'):
        print(attribute_classification_template)

    return attribute_classification_template

# IS(class1, class2) = any <=> IS(class2, class1) = any bc we wanna consider bidiretional associations ; edit if unidirectional eventually 
def association_prompt(c1_class, c1_attrs, c1_methods, c2_name, c2_attrs, c2_methods, readme, curr_associations):
    # format the methods for c1 and c2
    # p: param, t: type, d: description
    # name(param1: type1 (desc), param2: type2 (desc)) : return_type
    def format_method(name, details):
        params = []
        for param in details.get('params', []):
            # param can be (p, t) or (p, t, d)
            if len(param) == 3:
                p, t, d = param
                params.append(f"{p}: {t} ({d})")
            elif len(param) == 2:
                p, t = param
                params.append(f"{p}: {t}")
            else:
                params.append(str(param))
        method_str = f"{name}({', '.join(params)}) : {details.get('return_type', 'None')}"
        if 'doc' in details and details['doc']:
            method_str += f" ({details['doc']})"
        return method_str
    
    print(c1_methods)

    c1_methods_formatted = [
        format_method(name, details)
        for name, details in c1_methods
    ]
    c2_methods_formatted = [
        format_method(name, details)
        for name, details in c2_methods
    ]

    template = f"""
                ### Instruction:
                # Determine if the two given classes should contain an association.
                # Assume that it's always a bidirectional association. 
                # Consider:
                # 1. Invocation sites (field,array field,collection field, parameter,array parameter,collection parameter, local variable,local array,local collection) of class 2 in class 1 and vice versa 
                # 2. If one class appears as an attribute type in the other class
                # 3. If one class contains or aggregates the other class (list, set, map, array, etc.)
                # 4. If there's a clear semantic relationship or structural link between the classes
                # 5. If the classes are part of the same domain or context, indicating a potential conceptual link 

                # MUST keep the response concise ONLY limited to the output format.

                ### Examples of valid associations:
                - 'Order' class with attribute 'customer: Customer' should be associated with 'Customer' class
                - 'University' class with attribute 'departments: List<Department>' should be associated with 'Department' class
                - 'Student' class with attribute 'currentCourse: String' should be associated with 'Course' class
                
                ### readMe: 
                {readme}

                ### Class 1:
                Name: {c1_class}
                Attributes: {', '.join([f"{name}: {type_}" for name, type_ in c1_attrs]) if c1_attrs else 'None'}
                Methods: {', '.join(c1_methods_formatted) if c1_methods_formatted else 'None'}
                Current associations: {', '.join(curr_associations) if curr_associations and c1_class in curr_associations else 'None'}

                ### Class 2:
                Name: {c2_name}
                Attributes: {', '.join([f"{name}: {type_}" for name, type_ in c2_attrs]) if c2_attrs else 'None'}
                Methods: {', '.join(c2_methods_formatted) if c2_methods_formatted else 'None'}

                ### Example of output:
                {{
                "should_associate": true/false,
                "association_type": "association"/null,
                "direction": "class1_to_class2"/"class2_to_class1"/"bidirectional"/null
                }}
    """

    return template

# prompt with uncertainty quantification
def prompt_uq(readme,  domain_specific, implementation_details, tokenized_name):
    
    review_classification_template = f"""
                
                After your answer, provide the probability between 0.0 and 1.0 that your answer is correct or plausible for the 
                given task. Take your uncertainty in the prompt, the task difficulty, your knowledge availability and other sources of uncertainty into account. 
                Use the following format to respond: 
                "probability: [0.0-1.0]"

                ### Instruction:
                
                # Strictly classify whether the given class is Domain-specific (entity belonging to the field of the project) or an Implementation detail (feature, a data structure, a data type, database, or anything else pertaining to the project's specific implementation).

                # Heavily consider the TYPE of the software described in the following readMe and its architecture. 
                # Any class name containing a verb are examples of bad practice. Consider them as Implementation detail.  
    
                # MUST keep the response concise ONLY limited to the output format.
                
                ### Examples:

                - Health management system:
                + Domain-specific: 'doctor', 'patient', 'appointment', 'user', 'lab assistant'
                + implementation details: 'add doctor', 'doctor detail', 'doctor controller', 'lab report preview controller', 'user account controller', 'appointment success controller'

                - banking system:
                + Domain-specific: 'fund transfer', 'bank account', 'transaction service', 'account status', 'user'
                + implementation details: 'global error code', 'authenticate', 'internet banking user service application tests', 'app auth user filter', 'invalid banking user exception', 'user controller'

                - window management system:
                + Domain-specific: 'window', 'frame', 'panel', 'dialog', 'widget', 'tab', 'menu', 'toolbar', 'status bar', 'scroll bar'
                + implementation details: 'item contract', 'window rendering service', 'frame resizing controller', 'panel layout manager', 'dialog event listener', 'widget initialization handler', 'tab switch controller', 'menu item click listener', 'status bar updater', 'scroll bar drag controller'

                ### readMe:
                {readme}

                ### Current classifications:
                - Domain-specific: {', '.join(domain_specific) if domain_specific else 'None'}
                - Implementation detail: {', '.join(implementation_details) if implementation_details else 'None'}
                
                ### given class: '{tokenized_name}'

                ### Example of output:
                {{
                "class": [given class],
                "classification": "Domain-specific",
                "probability": [0.0-1.0]
                }}
                               
            """
    return review_classification_template

# prompt for class classification
def prompt(readme,  domain_specific, implementation_details, tokenized_name, attributes, methods):
    
    review_classification_template = f"""
                
                ### Instruction:
                
                # Strictly classify whether the given class is Domain-specific (entity belonging to the field of the project) or an Implementation detail (feature, a data structure, a data type, database, or anything else pertaining to the project's specific implementation).
                
                # Analyze the class name, attributes, and methods to infer its conceptual role.
                # Heavily consider the type of the software described in the following readMe and its architecture. 
                # Consider the context in which the software operates and the specific problem domain it addresses.
                # Any class name containing a verb are examples of bad practice. Consider them as Implementation detail.  
    
                # MUST keep the response concise ONLY limited to the output format.
                
                ### Examples:

                - Health management system:
                + Domain-specific: 'doctor', 'patient', 'appointment', 'user', 'lab assistant'
                + implementation details: 'add doctor', 'doctor detail', 'doctor controller', 'lab report preview controller', 'user account controller', 'appointment success controller'

                - banking system:
                + Domain-specific: 'fund transfer', 'bank account', 'transaction service', 'account status', 'user'
                + implementation details: 'global error code', 'authenticate', 'internet banking user service application tests', 'app auth user filter', 'invalid banking user exception', 'user controller', 'user data' 

                - window management system:
                + Domain-specific: 'window', 'frame', 'panel', 'dialog', 'widget', 'tab', 'menu', 'toolbar', 'status bar', 'scroll bar'
                + implementation details: 'item contract', 'window rendering service', 'frame resizing controller', 'panel layout manager', 'dialog event listener', 'widget initialization handler', 'tab switch controller', 'menu item click listener', 'status bar updater', 'scroll bar drag controller'

                ### readMe:
                {readme}

                ### Current classifications:
                - Domain-specific: {', '.join(domain_specific) if domain_specific else 'None'}
                - Implementation detail: {', '.join(implementation_details) if implementation_details else 'None'}
                
                ### given class name: '{tokenized_name}'
                ### given class attributes: '{attributes}'
                ### given class methods: '{methods}'

                ### Example of output:
                {{
                "class": [given class],
                "classification": "Domain-specific"
\                }}
                               
            """
    return review_classification_template
