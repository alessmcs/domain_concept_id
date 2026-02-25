import random
import string
import xml.etree.ElementTree as ET
import sys
import uuid

# Helper function to find the parent of an element
def find_parent(root, child):
    for parent in root.iter():
        if child in parent:
            return parent
    return None

def remove_implementation_classes(xml_path, implementation_classes):
    # Parse the XML file
    tree = ET.parse(xml_path)
    root = tree.getroot()

    assos_to_create = []
    # print(root.tag)

    # Step 1: Find all classes and store their IDs
    class_map = {}  # {class_id: class_element}
    for clazz in root.findall(".//Class"):
        class_id = clazz.get("Id")
        if class_id is not None:
            class_map[class_id] = clazz

    # print(class_map)

    # Step 2: Identify implementation classes based on names
    implementation_ids = set()
    for class_id, clazz in class_map.items():
        # print(clazz.get("Name"))
        if clazz.get("Name") in implementation_classes:
            implementation_ids.add(class_id)

    # print(f"Implementation IDs: {implementation_ids}")

    # Step 3: Remove implementation classes with live updates
    for class_id in implementation_ids:
        clazz = class_map[class_id]
        parent = find_parent(root, clazz)  # Find parent manually
        if parent is not None:
            # Print before removal
            print(f"Removing Class: {clazz.get('Name')} from parent: {parent.tag}")
            parent.remove(clazz)

    # Step 4: Remove relationships and connectors related to implementation classes
    def remove_related_elements(tag, attr_from, attr_to):
        for relation in root.findall(f".//{tag}"):
            # print relation for debugging
            print(f"\nRelation: {relation.tag}")
            from_id = relation.get(attr_from)
            to_id = relation.get(attr_to)
            relation_id = relation.get("Id")
            if from_id in implementation_ids or to_id in implementation_ids:
                # print id and its corresponding implementation class name using map class_map = {}  # {class_id: class_element}
                print(f"Removing {tag} from {class_map[from_id].get('Name')} to {class_map[to_id].get('Name')}")
                parent = find_parent(root, relation)
                if parent is not None:
                    print(f"Parent: {parent.tag}")
                    print(f"Removing relation: {relation.tag} from parent: {parent.tag}, id is {relation_id}")
                    parent.remove(relation)
                    remove_connectors(tag, relation_id) # Remove the connector even if we removed the relation to avoid bugs in VP 


    def remove_connectors(tag, id):
        # Remove connectors whose tag matches and whose MetaModelElement attribute matches any implementation_id
        for connector in root.findall(f".//Connectors/{tag}"):
            meta_model_element = connector.get("MetaModelElement")
            if meta_model_element == id:
                print(f"Removing Connector: {connector.tag} with MetaModelElement: {meta_model_element}")
                parent = find_parent(root, connector)
                if parent is not None:
                    parent.remove(connector)


    # Check for relations dynamically and process them if they exist
    relation_types = [
        ("Association", "EndRelationshipFromMetaModelElement", "EndRelationshipToMetaModelElement"),
        ("Realization", "From", "To"),
        ("Generalization", "From", "To"),
        ("Containment", "From", "To"),
        ("Dependency", "From", "To"),
        ("Aggregation", "From", "To")
    ]

    for tag, attr_from, attr_to in relation_types:
        if root.findall(f".//{tag}"):
            print(f"Processing relation: {tag}")
            remove_related_elements(tag, attr_from, attr_to)
            # remove_connectors(tag, attr_from, attr_to)
        else:
            print(f"No relation found for: {tag}")

    # Step 5: Save the modified XML back to the file
    output_xml_path = xml_path.replace(".xml", "_modified_1.xml")
    with open(output_xml_path, "w", encoding="utf-8") as f:
        pass  
    tree.write(output_xml_path, encoding="utf-8", xml_declaration=True)
    print(f"Modified XML saved to: {output_xml_path}")

    # TODO remove any classes in ModelRelationshipContainer (there has to be a quicker/less brute-force way to do it )

    return output_xml_path

def get_class_methods(class_element):
        methods = class_element.findall(".//Operation")
        method_names = [method.get("Name") for method in methods]
        method_ids = [method.get("Id") for method in methods]

        return dict(zip(method_names, method_ids))

def remove_constructor(old_xml_path, xml_path, class_name):

    tree = ET.parse(old_xml_path)
    root = tree.getroot()   
    class_element = root.find(f".//Class[@Name='{class_name}']")

    if class_element is None:
        print(f"Class '{class_name}' not found in XML.")
        return

    model_children = class_element.find("ModelChildren")
    if model_children is None:
        print("No ModelChildren found for class", class_element.get("Name"))
        return

    operations = model_children.findall(f"./Operation[@Name='{class_name}']") # Find all the constructors (possible duplicates)

    for o in operations:
        # print(ET.tostring(o, encoding='unicode'))
        model_children.remove(o)

    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    print(f"Removed constructor(s) from class {class_name} and saved to {xml_path}.")

    return ET.tostring(root, encoding='unicode')


def remove_getters_setters(xml_string, output_xml_path, class_name):
    """
    Remove getter/setter pairs from a class in the XML
    """
    print(f"File being passed to remove_getters_setters: {output_xml_path}")

    try: 
        tree = ET.parse(xml_string)
        root = tree.getroot()   
        
        class_element = root.find(f".//Class[@Name='{class_name}']")
        if class_element is None:
            print(f"Class '{class_name}' not found in XML.")
            # Write original XML to file
            tree = ET.ElementTree(root)
            tree.write(output_xml_path, encoding="utf-8", xml_declaration=True)
            return output_xml_path

        methods = get_class_methods(class_element)
        method_names = list(methods.keys())
        model_children = class_element.find("ModelChildren")

        if model_children is None:
            print("No ModelChildren found for class", class_element.get("Name"))
            tree = ET.ElementTree(root)
            tree.write(output_xml_path, encoding="utf-8", xml_declaration=True)
            return output_xml_path
        
        # Get all operations
        operations = model_children.findall("./Operation")

        # Get all attributes to make sure they're getters/setters
        attributes = model_children.findall("./Attribute")
        attr_names = [attr.get("Name").lower() for attr in attributes]
        print(attr_names)

        # Track processed methods to avoid duplicates
        processed_methods = set()
        operations_to_remove = []  # Collect operations to remove

        for m in method_names:
            if m in processed_methods:
                continue
                
            # Handle getters
            if m.startswith("get") and len(m) > 3:
                root_name = m[3:]
                setter_name = f"set{root_name}"
                if setter_name in method_names and root_name.lower() in attr_names:
                    print(f"{m} has a corresponding setter: {setter_name} for attribute {root_name.lower()}")
                    
                    # Find operations to remove
                    for op in operations:
                        name = op.attrib.get("Name")
                        if name == m or name == setter_name:
                            operations_to_remove.append(op)
                            print(f"Marking for removal: {name}")
                    
                    processed_methods.add(m)
                    processed_methods.add(setter_name)
                        
            # Handle setters (only if not already processed)
            elif m.startswith("set") and len(m) > 3 and m not in processed_methods:
                root_name = m[3:]
                getter_name = f"get{root_name}"
                if getter_name in method_names and root_name.lower() in attr_names:
                    print(f"{m} has a corresponding getter: {getter_name}")
                    
                    # Find operations to remove
                    for op in operations:
                        name = op.attrib.get("Name")
                        if name == m or name == getter_name:
                            operations_to_remove.append(op)
                            print(f"Marking for removal: {name}")
                    
                    processed_methods.add(m)
                    processed_methods.add(getter_name)
        
        # Remove all marked operations at once (moved outside the loop)
        for op in operations_to_remove:
            if op in model_children:
                model_children.remove(op)
                print(f"Removed: {op.get('Name')}")

        # Write the modified XML to file
        tree = ET.ElementTree(root)
        tree.write(output_xml_path, encoding="utf-8", xml_declaration=True)
        print(f"Removed getters & setters from class {class_name} and saved to {output_xml_path}.")
        
        return output_xml_path

    except Exception as e: 
        print(f"Error in remove_getters_setters: {e}")
        # Write original XML to file in case of error
        try:
            root = ET.fromstring(xml_string)
            tree = ET.ElementTree(root)
            tree.write(output_xml_path, encoding="utf-8", xml_declaration=True)
        except:
            print("Failed to write fallback XML")
        return output_xml_path
         

def remove_irrelevant_attrs(irrelevant, class_name, xml_path):

    # TODO: maybe clean up other parts of the xml containing the unwanted attributes 
    
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # find all attributes from the irrelevant list
    for attr_name in [attr[0] for attr in irrelevant]:
        # find the class element by name
        class_element = root.find(f".//Class[@Name='{class_name}']")
        if class_element is not None:
            # find the attribute element by name
            attr_element = class_element.find(f".//ModelChildren/Attribute[@Name='{attr_name}']")
            if attr_element is not None:
                # remove the attribute element
                parent = find_parent(class_element, attr_element)
                if parent is not None:
                    parent.remove(attr_element)
                    print(f"Removed attribute '{attr_name}' from class '{class_name}'")
        else:
            print(f"Class '{class_name}' not found in XML.")

    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    print(f"Modified XML saved to: {xml_path} with irrelevant attributes removed.")

    return xml_path

def remove_irrelevant_methods(irrelevant, class_name, output_xml_path):

    print(f"Removing irrelevant methods from class: {class_name}")
    print(irrelevant)
    # Parse the XML file
    tree = ET.parse(output_xml_path)
    root = tree.getroot()

    # Find the class element by name

    class_element = root.find(f".//Class[@Name='{class_name}']")
    if class_element is None:
        print(f"Class '{class_name}' not found.")
        return output_xml_path
    
    print(f"Found class '{class_name}':")
    
    model_children = class_element.find("ModelChildren")
    if model_children is None:
        print("No ModelChildren found in class")
        return output_xml_path

    for method_name in irrelevant:
        # Look for Operation directly under ModelChildren
        operations = model_children.findall("Operation[@Name='{}']".format(method_name))
        for op in operations:
            print(f"Found method {method_name}, removing...")
            model_children.remove(op)
            print(f"Removed method {method_name}")

    # for class_element in class_elements:
    #     for method_name in irrelevant:
    #         method_element = class_element.find(f"./ModelChildren/Operation[@Name='{method_name}']") 
    #         if method_element is not None:
    #             print("found method", method_name)
    #             parent = find_parent(class_element, method_element)
    #             if parent is not None:
    #                 print(f"Removing method '{method_name}' from parent '{parent.tag}'")
    #                 parent.remove(method_element)
    #             else:
    #                 print(f"Could not remove method '{method_name}' because parent was not found.")

    # Remove also from the <package> section 
    # TODO: find the part of the xml that affects the displaying of the classes & methods 

    tree.write(output_xml_path, encoding="utf-8", xml_declaration=True)
    print(f"Modified XML saved to: {output_xml_path} with irrelevant methods removed.")

    return output_xml_path

def generate_vp_id():
    """
    Generate a 16-character ID similar to Visual Paradigm's format.
    VP uses base64-like encoding with alphanumeric characters.
    """
    # VP uses alphanumeric characters (A-Z, a-z, 0-9)
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=16))

def build_xml_association(from_class, from_class_shape, to_class, to_class_shape, z_order, xml_path):
    # Removed any specific or generated information, hopefully VP handles it lol 

    from_class_id = from_class.get("Id", "")
    from_shape_id = from_class_shape.get("Id", "") if from_class_shape is not None else ""

    if not from_class_id:
        print("Source class ID is empty")
        return
    
    to_class_id = to_class.get("Id", "")
    if not to_class_id:
        print("Target class ID is empty")
        return

    to_class_name = to_class.get("Name", "")
    if not to_class_name:
        print("Target class name is empty")
        return
    
    to_shape_id = to_class_shape.get("Id", "") if to_class_shape is not None else ""
    
    uid_1 = generate_vp_id()  # model element 
    uid_2 = generate_vp_id()
    uid_3 = generate_vp_id()
    uid_4 = generate_vp_id()
    uid_5 = generate_vp_id()
    uid_6 = generate_vp_id() # graphical element (shape) 

    # The part in <ModelRelationshipContainer>
    mrc_section = f'''\n<Association Abstract="false" BacklogActivityId="0" Derived="false" Direction="From To" Documentation_plain="" EndRelationshipFromMetaModelElement="{from_class_id}" EndRelationshipToMetaModelElement="{to_class_id}" FinalSpecialization="false" Id="{uid_1}" Leaf="false" OrderingInProfile="-1" PmAuthor="" PmCreateDateTime="" PmLastModified="" QualityReason_IsNull="true" QualityScore="-1" UserIDLastNumericValue="0" UserID_IsNull="true" Visibility="Unspecified">
							<FromEnd>
								<AssociationEnd AggregationKind="None" BacklogActivityId="0" ConnectToCodeModel="1" DefaultValue_IsNull="true" Derived="false" DerivedUnion="false" Documentation_plain="" EndModelElement="{from_class_id}" Id="{uid_2}" JavaCodeAttributeName="" Leaf="false" Multiplicity="Unspecified" Navigable="Non Navigable" PmAuthor="" PmCreateDateTime="" PmLastModified_IsNull="true" ProvidePropertyGetterMethod="false" ProvidePropertySetterMethod="false" QualityReason_IsNull="true" QualityScore="-1" ReadOnly="false" Static="false" TypeModifier="" UserIDLastNumericValue="0" UserID_IsNull="true" Visibility="Unspecified">
									<Qualifier>
										<Qualifier BacklogActivityId="0" Documentation_plain="" Id="{uid_3}" Name="" PmAuthor="" PmCreateDateTime="" PmLastModified_IsNull="true" QualityReason_IsNull="true" QualityScore="-1" UserIDLastNumericValue="0" UserID_IsNull="true" />
									</Qualifier>
								</AssociationEnd>
							</FromEnd>
							<ToEnd>
								<AssociationEnd AggregationKind="None" BacklogActivityId="0" ConnectToCodeModel="1" DefaultValue_IsNull="true" Derived="false" DerivedUnion="false" EndModelElement="{to_class_id}" Id="{uid_4}" JavaCodeAttributeName="" Leaf="false" Multiplicity="1" Name="" Navigable="Navigable" PmAuthor="alessandramancas" PmCreateDateTime="" PmLastModified_IsNull="true" ProvidePropertyGetterMethod="true" ProvidePropertySetterMethod="true" QualityReason_IsNull="true" QualityScore="-1" ReadOnly="false" RepresentativeAttribute="" Static="false" TypeModifier_IsNull="true" UserIDLastNumericValue="0" UserID_IsNull="true" Visibility="private">
									<Qualifier>
										<Qualifier BacklogActivityId="0" Documentation_plain="" Id="{uid_5}" Name="" PmAuthor="alessandramancas" PmCreateDateTime="" PmLastModified_IsNull="true" QualityReason_IsNull="true" QualityScore="-1" UserIDLastNumericValue="0" UserID_IsNull="true" />
									</Qualifier>
									<Type>
										<Class Idref="{to_class_id}" Name="{to_class_name}" />
									</Type>
								</AssociationEnd>
							</ToEnd>
						</Association>'''

    # <Association Abstract="false" BacklogActivityId="0" Derived="false" Direction="From To" Documentation_plain="" EndRelationshipFromMetaModelElement="FROM_MODEL_ID" EndRelationshipToMetaModelElement="TO_MODEL_ID" FinalSpecialization="false" Id="UID_1" Leaf="false" OrderingInProfile="-1" PmAuthor="alessandramancas" PmCreateDateTime="2025-06-18T15:29:43.143" PmLastModified="2025-06-18T15:29:56.452" QualityReason_IsNull="true" QualityScore="-1" UserIDLastNumericValue="0" UserID_IsNull="true" Visibility="Unspecified">
	# 						<FromEnd>
	# 							<AssociationEnd AggregationKind="None" BacklogActivityId="0" ConnectToCodeModel="1" DefaultValue_IsNull="true" Derived="false" DerivedUnion="false" Documentation_plain="" EndModelElement="FROM_MODEL_ID" Id="UID_2" JavaCodeAttributeName="" Leaf="false" Multiplicity="Unspecified" Navigable="Non Navigable" PmAuthor="alessandramancas" PmCreateDateTime="2025-06-18T15:29:43.143" PmLastModified_IsNull="true" ProvidePropertyGetterMethod="false" ProvidePropertySetterMethod="false" QualityReason_IsNull="true" QualityScore="-1" ReadOnly="false" Static="false" TypeModifier="" UserIDLastNumericValue="0" UserID_IsNull="true" Visibility="Unspecified">
	# 								<Qualifier>
	# 									<Qualifier BacklogActivityId="0" Documentation_plain="" Id="UID_3" Name="" PmAuthor="alessandramancas" PmCreateDateTime="2025-06-18T15:29:43.143" PmLastModified_IsNull="true" QualityReason_IsNull="true" QualityScore="-1" UserIDLastNumericValue="0" UserID_IsNull="true"/>
	# 								</Qualifier>
	# 							</AssociationEnd>
	# 						</FromEnd>
	# 						<ToEnd>
	# 							<AssociationEnd AggregationKind="None" BacklogActivityId="0" ConnectToCodeModel="1" DefaultValue_IsNull="true" Derived="false" DerivedUnion="false" EndModelElement="TO_MODEL_ID" Id="UID_4" JavaCodeAttributeName="" Leaf="false" Multiplicity="1" Name="cameraManager" Navigable="Navigable" PmAuthor="alessandramancas" PmCreateDateTime="2025-06-18T15:29:43.143" PmLastModified_IsNull="true" ProvidePropertyGetterMethod="false" ProvidePropertySetterMethod="false" QualityReason_IsNull="true" QualityScore="-1" ReadOnly="false" RepresentativeAttribute="x8MhIemAUOn6IhDE" Static="false" TypeModifier_IsNull="true" UserIDLastNumericValue="0" UserID_IsNull="true" Visibility="private">
	# 								<Qualifier>
	# 									<Qualifier BacklogActivityId="0" Documentation_plain="" Id="5yMhIemAUOn6IhSD" Name="" PmAuthor="alessandramancas" PmCreateDateTime="2025-06-18T15:29:43.143" PmLastModified_IsNull="true" QualityReason_IsNull="true" QualityScore="-1" UserIDLastNumericValue="0" UserID_IsNull="true"/>
	# 								</Qualifier>
	# 								<Type>
	# 									<Class Idref="TO_MODEL_ID" Name="NAME"/>
	# 								</Type>
	# 							</AssociationEnd>
	# 						</ToEnd>

    # The part in <Connectors>

    # compute x, y, z_order, width and height for the connector element 
    x1, x2, y1, y2, new_z_order = calc_x_y_z(from_class, to_class, z_order, xml_path)

    width = max(x1, x2) - min(x1, x2)
    height = max(y1, y2) - min(y1, y2)
    x = min(x1, x2)
    y = min(y1, y2)

    connectors_section = f'''\n<Association AssociationEndPropertyStringsAInternalHeight="-2147483648" \
        AssociationEndPropertyStringsAInternalWidth="-2147483648" AssociationEndPropertyStringsBInternalHeight="-2147483648" \
            AssociationEndPropertyStringsBInternalWidth="-2147483648" Background="rgb(122, 207, 245)" ConnectorLabelOrientation="4" \
                ConnectorLineJumps="4" ConnectorStyle="Follow Diagram" Foreground="rgb(0, 0, 0)" From="{from_shape_id}" FromConnectType="0" \
                    FromMultiplicityInternalHeight="-2147483648" FromMultiplicityInternalWidth="-2147483648" FromPinType="1" \
                        FromRoleInternalHeight="-2147483648" FromRoleInternalWidth="-2147483648" FromShapeXDiff="0" \
                            FromShapeYDiff="0" HasAssociationEndPropertyStringsAShape="false" HasAssociationEndPropertyStringsBShape="false" \
                                HasMultiplicityAShape="false" HasMultiplicityBShape="true" HasRoleAShape="false" HasRoleBShape="true" \
                                    Height="{height}" Id="{uid_6}" MetaModelElement="{uid_1}" Model="{uid_1}" ModelElementNameAlignment="9" \
                                        PaintThroughLabel="2" RequestRebuild="false" RequestRebuildFromEnd="false" RequestRebuildToEnd="false" \
                                            RequestResetCaption="false" RequestResetCaptionFitWidth="false" RequestResetCaptionSize="false" \
                                                Selectable="true" ShowAssociationEndPropertyStrings="false" ShowConnectorName="2" \
                                                    ShowDirection="false" ShowFromMultiplicity="true" ShowFromRoleName="true" \
                                                        ShowFromRoleVisibility="true" ShowMultiplicityConstraints="false" ShowNavigationArrows="0" ShowOrderedMultiplicityConstraint="true" ShowStereotypes="true" ShowToMultiplicity="true" ShowToRoleName="true" ShowToRoleVisibility="true" ShowUniqueMultiplicityConstraint="true" SuppressImplied1MultiplicityForAssociationEnd="0" To="{to_shape_id}" ToConnectType="0" ToMultiplicityInternalHeight="-2147483648" ToMultiplicityInternalWidth="-2147483648" ToPinType="1" ToRoleInternalHeight="-2147483648" ToRoleInternalWidth="-2147483648" ToShapeXDiff="0" ToShapeYDiff="0" UseFromShapeCenter="false" UseToShapeCenter="false" Width="{width}" X="{x}" Y="{y}" ZOrder="{new_z_order}">
					<Line Cap="0" Color="rgb(0, 0, 0)" Transparency="0" Weight="1.0">
						<Stroke/>
					</Line>
					<Points>
						<Point X="{x1}" Y="{y1}"/>
						<Point X="{x2}" Y="{y2}"/>
					</Points>
				</Association>'''
    
    print("MetaModelElement in mrc:", uid_1)
    print("Association ID in connectors", uid_6)

    # <Association AssociationEndPropertyStringsAInternalHeight="-2147483648" AssociationEndPropertyStringsAInternalWidth="-2147483648" AssociationEndPropertyStringsBInternalHeight="-2147483648" AssociationEndPropertyStringsBInternalWidth="-2147483648" Background="rgb(122, 207, 245)" ConnectorLabelOrientation="4" ConnectorLineJumps="4" ConnectorStyle="Follow Diagram" Foreground="rgb(0, 0, 0)" From="FROM_SHAPES_ID" FromConnectType="0" FromMultiplicityInternalHeight="-2147483648" FromMultiplicityInternalWidth="-2147483648" FromPinType="1" FromRoleInternalHeight="-2147483648" FromRoleInternalWidth="-2147483648" FromShapeXDiff="0" FromShapeYDiff="0" HasAssociationEndPropertyStringsAShape="false" HasAssociationEndPropertyStringsBShape="false" HasMultiplicityAShape="false" HasMultiplicityBShape="true" HasRoleAShape="false" HasRoleBShape="true" Height="215" Id="UID_5" MetaModelElement="MODEL_ASSO_ID" Model="MODEL_ASSO_ID" ModelElementNameAlignment="9" PaintThroughLabel="2" RequestRebuild="false" RequestRebuildFromEnd="false" RequestRebuildToEnd="false" RequestResetCaption="false" RequestResetCaptionFitWidth="false" RequestResetCaptionSize="false" Selectable="true" ShowAssociationEndPropertyStrings="false" ShowConnectorName="2" ShowDirection="false" ShowFromMultiplicity="true" ShowFromRoleName="true" ShowFromRoleVisibility="true" ShowMultiplicityConstraints="false" ShowNavigationArrows="0" ShowOrderedMultiplicityConstraint="true" ShowStereotypes="true" ShowToMultiplicity="true" ShowToRoleName="true" ShowToRoleVisibility="true" ShowUniqueMultiplicityConstraint="true" SuppressImplied1MultiplicityForAssociationEnd="0" To="TO_SHAPE_ID" ToConnectType="0" ToMultiplicityInternalHeight="-2147483648" ToMultiplicityInternalWidth="-2147483648" ToPinType="1" ToRoleInternalHeight="-2147483648" ToRoleInternalWidth="-2147483648" ToShapeXDiff="0" ToShapeYDiff="0" UseFromShapeCenter="false" UseToShapeCenter="false" Width="100" X="1887" Y="1541" ZOrder="238">
	# 				<MultiplicityBRectangle Height="40" Width="40" X="1930" Y="1577"/>
	# 				<ElementFont Color="rgb(0, 0, 0)" Name="Dialog" Size="11" Style="0"/>
	# 				<Line Cap="0" Color="rgb(0, 0, 0)" Transparency="0" Weight="1.0">
	# 					<Stroke/>
	# 				</Line>
	# 				<Caption Height="0" InternalHeight="-2147483648" InternalWidth="-2147483648" Side="None" Visible="true" Width="20" X="1947" Y="1667"/>
	# 				<RoleB>
	# 					<NameCaption Height="78" Width="78" X="1857" Y="1559"/>
	# 					<MultiplicityCaption Height="40" Width="40" X="1930" Y="1577"/>
	# 				</RoleB>
	# 				<Points>
	# 					<Point X="1937.0" Y="1706.0"/>
	# 					<Point X="1937.0" Y="1591.0"/>
	# 				</Points>
	# 			</Association>

    return mrc_section, connectors_section


def find_edge_connection_points(class1, class2):
    # Calculate centers
    c1x = class1['x'] + (class1['width'] / 2)
    c1y = class1['y'] + (class1['height'] / 2)
    c2x = class2['x'] + (class2['width'] / 2)
    c2y = class2['y'] + (class2['height'] / 2)

    # Determine which edges to connect based on relative positions
    if abs(c1x - c2x) > abs(c1y - c2y):
        # Connect left/right edges
        if c1x < c2x:
            x1 = class1['x'] + class1['width']  # Right edge of class1
            x2 = class2['x']                     # Left edge of class2
        else:
            x1 = class1['x']                     # Left edge of class1
            x2 = class2['x'] + class2['width']  # Right edge of class2
        y1 = c1y
        y2 = c2y
    else:
        # Connect top/bottom edges
        if c1y < c2y:
            y1 = class1['y'] + class1['height']  # Bottom edge of class1
            y2 = class2['y']                        # Top edge of class2
        else:
            y1 = class1['y']                        # Top edge of class1
            y2 = class2['y'] + class2['height']   # Bottom edge of class2
        x1 = c1x
        x2 = c2x
    
    return x1, x2, y1, y2

def calc_x_y_z(from_class_element, to_class_element, prev_z_order, xml_path):

    # print the class elements for debugging
    print("From Class Element:", from_class_element.attrib)
    print("To Class Element:", to_class_element.attrib)

    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Find the class element by name
    from_class_element_shape = root.find(f".//Shapes/Class[@Name='{from_class_element.get('Name')}']")
    if from_class_element_shape is None:
        print(f"Class '{from_class}' not found in XML.")
        return
    
    to_class_element_shape = root.find(f".//Shapes/Class[@Name='{to_class_element.get('Name')}']")
    if to_class_element_shape is None:
        print(f"Class '{to_class_element.get('Name')}' not found in XML.")
        return
    
    print("From Class Element SHAPEEEEE:", from_class_element_shape.attrib)

    # Get the dimensions and position of the from_class
    from_class = {
        "x": float(from_class_element_shape.get("X", 0)),
        "y": float(from_class_element_shape.get("Y", 0)),
        "width": float(from_class_element_shape.get("Width", 0)),
        "height": float(from_class_element_shape.get("Height", 0)),
        "id": from_class_element_shape.get("Id", "")
    }

    to_class = {
        "x": float(to_class_element_shape.get("X", 0)),
        "y": float(to_class_element_shape.get("Y", 0)),
        "width": float(to_class_element_shape.get("Width", 0)),
        "height": float(to_class_element_shape.get("Height", 0)),
        "id": to_class_element_shape.get("Id", "")
    }

    print(from_class)
    print(to_class) 

    # Get the connection points
    x1, x2, y1, y2 = find_edge_connection_points(from_class, to_class)
    print(x1, x2, y1, y2)

    # Calculate the z-order
    z_order = prev_z_order + 2

    return x1, x2, y1, y2, z_order   

def add_association_to_xml(xml_path, from_class_id, from_class_name, to_class_id, to_class_name):
    # Parse the XML file
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # find the 2 classes we want to work with
    from_class_element = root.find(f".//Class[@Id='{from_class_id}']")
    if from_class_element is None:
        print(f"Class '{from_class_id}' not found in XML.")
        return

    from_class_shape = root.find(f".//Shapes/Class[@Name='{from_class_name}']")

    to_class_element = root.find(f".//Class[@Id='{to_class_id}']")
    if to_class_element is None:
        print(f"Class '{to_class_id}' not found in XML.")
        return

    to_class_shape = root.find(f".//Shapes/Class[@Name='{to_class_name}']")
    
    relationships_container = root.find(".//ModelRelationshipContainer[@Name='relationships']")

    # Find the ModelRelationshipContainer (model element for each association)
    mrc_container = relationships_container.find(".//ModelRelationshipContainer[@Name='Association']")
    if mrc_container is None:
        # If it doesn't exist, create it
        print("ModelRelationshipContainer not found, creating it")

        mc = relationships_container.find(".//ModelChildren")
        mrc_container = ET.Element("ModelRelationshipContainer", Name="Association")
        mc.append(mrc_container)
    
    # Find the Connectors container (graphical aspect of each association)

    connectors_container = root.find(".//Connectors")
    if connectors_container is None:
        parent = root.find(".//Diagrams/ClassDiagram")
        connectors_container = ET.Element("Connectors")
        parent.append(connectors_container)
    

    # Calculate the highest z order so far
    existing_associations = mrc_container.findall(".//Association")
    prev_z_order = 0
    if existing_associations:
        z_orders = [int(assoc.get("ZOrder", 0)) for assoc in existing_associations if assoc.get("ZOrder") is not None]
        prev_z_order = max(z_orders) if z_orders else 0

    # Create the new Association element
    association_element, connectors_element = build_xml_association(from_class_element, from_class_shape, to_class_element, to_class_shape, prev_z_order, xml_path)

    mrc_container.append(ET.fromstring(association_element))
    print("model element added")
    connectors_container.append(ET.fromstring(connectors_element))
    print("connector added")

    # Save the modified XML back to the file
    import os

    output_xml_path = xml_path.replace("_modified.xml", "_with_associations.xml")

    # Ensure the output file exists and is empty
    with open(output_xml_path, "w", encoding="utf-8") as f:
        pass  # This will create the file if it doesn't exist, or clear it if it does

    tree.write(output_xml_path, encoding="utf-8", xml_declaration=True)
    print(f"Association added to {output_xml_path} ML: {from_class_id} -> {to_class_name} (ID: {to_class_id})")

    return output_xml_path


if __name__ == "__main__":
    # Example usage
    input_xml_path = "path/to/model"  # Path to the input XML file of ur own

    # here is an exmaple of what can implementation_classes be
    implementation_classes = [
        "Patient"                                       
    ]


    # testing to remove irrelevant attrs
    test_xml = "data/Espresso/project_modified3.xml"

    remove_getters_setters(test_xml, "PackageAndCompanyPairs")



    # todo: create a test file to avoid running the whole thing every time 
    # test_file = "/u/mancasat/Desktop/summer_intern/domain-concepts-identification-using-LLMs-aless/data/testing/test-getters-setters.xml"

    # tree = ET.parse(test_file)
    # root = tree.getroot()

    # for clazz in root.findall(".//Class"):
    #     print("Class: ", clazz.attrib.get("Name"))
    #     remove_getters_setters(test_file, clazz, tree)

    
    # output_xml_path = test_file.replace(".xml", "_modified.xml")
    # tree.write(output_xml_path, encoding="utf-8", xml_declaration=True)
    # print(f"Modified XML saved to: {output_xml_path}")

    


    #remove_implementation_classes(input_xml_path, implementation_classes)

