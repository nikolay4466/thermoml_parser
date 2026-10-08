import json
import re


def as_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def make_column_name(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)

    return text.strip("_")


def first_real_value(dictionary):
    for key, value in dictionary.items():
        if key != "tml_elements":
            return value

    return None


def get_org_num(dictionary):
    return (
        dictionary
        .get("RegNum", {})
        .get("nOrgNum")
    )


def get_phase(dictionary, block_name, field_name):
    phases = []

    for block in as_list(dictionary.get(block_name)):
        phase = block.get(field_name)

        if phase is not None:
            phases.append(str(phase))

    return " | ".join(phases) if phases else None


def parse_file(json_path):

    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    rows = []

                                                              
                               
                                                              

    citation = data.get("Citation", {})

    common_data = {
        "source_file": json_path.name,
        "doi": citation.get("sDOI"),
        "year": citation.get("yrPubYr"),
        "title": citation.get("sTitle"),
    }

                                                              
                         
                                
                                                              

    compounds = {}

    for compound in as_list(data.get("Compound")):

        org_num = get_org_num(compound)

        names = as_list(
            compound.get("sCommonName")
        )

        compounds[org_num] = {
            "name": names[0] if names else None,
            "formula": compound.get("sFormulaMolec"),
            "inchi": compound.get("sStandardInChI"),
            "inchikey": compound.get("sStandardInChIKey"),
        }

                                                              
                       
                                                              

    for experiment in as_list(
        data.get("PureOrMixtureData")
    ):

        experiment_data = common_data.copy()

        experiment_data["data_block"] = (
            experiment.get("nPureOrMixtureDataNumber")
        )

                                                              
                    
                                                              

        component_number = {}

        for i, component in enumerate(
            as_list(experiment.get("Component")),
            start=1
        ):

            org_num = get_org_num(component)
            component_number[org_num] = i

            compound = compounds.get(org_num, {})

            experiment_data[f"component_{i}_name"] = (
                compound.get("name")
            )

            experiment_data[f"component_{i}_formula"] = (
                compound.get("formula")
            )

            experiment_data[f"component_{i}_inchi"] = (
                compound.get("inchi")
            )

            experiment_data[f"component_{i}_inchikey"] = (
                compound.get("inchikey")
            )

                                                              
                   
                                         
                                                              

        variable_map = {}

        for variable in as_list(
            experiment.get("Variable")
        ):

            var_number = variable.get("nVarNumber")

            variable_id = variable.get(
                "VariableID",
                {}
            )

            variable_type = variable_id.get(
                "VariableType",
                {}
            )

            label = first_real_value(variable_type)

            if label is None:
                continue

            column = make_column_name(label)

                                                   
                                                
            org_num = get_org_num(variable_id)

            if org_num in component_number:
                i = component_number[org_num]
                column = f"component_{i}_{column}"

            variable_map[var_number] = {
                "column": column,
                "phase": get_phase(
                    variable,
                    "VarPhaseID",
                    "eVarPhase"
                ),
            }

                                                              
                     
                                         
                                                              

        for constraint in as_list(
            experiment.get("Constraint")
        ):

            constraint_id = constraint.get(
                "ConstraintID",
                {}
            )

            constraint_type = constraint_id.get(
                "ConstraintType",
                {}
            )

            label = first_real_value(
                constraint_type
            )

            if label is None:
                continue

            column = make_column_name(label)

            org_num = get_org_num(constraint_id)

            if org_num in component_number:
                i = component_number[org_num]
                column = f"component_{i}_{column}"

            experiment_data[column] = (
                constraint.get("nConstraintValue")
            )

            experiment_data[f"{column}_digits"] = (
                constraint.get("nConstrDigits")
            )

            experiment_data[f"{column}_phase"] = (
                get_phase(
                    constraint,
                    "ConstraintPhaseID",
                    "eConstraintPhase"
                )
            )

                                                              
                   
                                          
                                                              

        property_map = {}

        for prop in as_list(
            experiment.get("Property")
        ):

            prop_number = prop.get("nPropNumber")

            property_method = prop.get(
                "Property-MethodID",
                {}
            )

            group = property_method.get(
                "PropertyGroup",
                {}
            )

            group_name = next(
                (
                    key
                    for key in group
                    if key != "tml_elements"
                ),
                None
            )

            group_data = (
                group.get(group_name, {})
                if group_name
                else {}
            )

            property_org_num = get_org_num(
                property_method
            )

            property_component = None
            property_component_name = None

            if property_org_num in component_number:
                i = component_number[property_org_num]
                property_component = f"component_{i}"

            if property_org_num in compounds:
                property_component_name = (
                    compounds[property_org_num]
                    .get("name")
                )

            property_map[prop_number] = {
                "name": group_data.get("ePropName"),
                "method": group_data.get("eMethodName"),
                "phase": get_phase(
                    prop,
                    "PropPhaseID",
                    "ePropPhase"
                ),
                "component": property_component,
                "component_name": property_component_name,
            }

                                                              
                    
                                                       
                                                              

        for point_number, point in enumerate(
            as_list(experiment.get("NumValues")),
            start=1
        ):

            row = experiment_data.copy()
            row["point_number"] = point_number

                           
            for value in as_list(
                point.get("VariableValue")
            ):

                var_number = value.get("nVarNumber")
                variable = variable_map.get(var_number)

                if variable is None:
                    continue

                column = variable["column"]

                row[column] = value.get("nVarValue")

                row[f"{column}_digits"] = (
                    value.get("nVarDigits")
                )

                row[f"{column}_phase"] = (
                    variable.get("phase")
                )

                           
                                                             
            for property_value in as_list(
                point.get("PropertyValue")
            ):

                final_row = row.copy()

                prop_number = (
                    property_value.get("nPropNumber")
                )

                prop = property_map.get(
                    prop_number,
                    {}
                )

                full_name = prop.get("name")

                if full_name and ", " in full_name:
                    property_name, property_unit = (
                        full_name.rsplit(", ", 1)
                    )
                else:
                    property_name = full_name
                    property_unit = None

                final_row["property_name"] = (
                    property_name
                )

                final_row["property_unit"] = (
                    property_unit
                )

                final_row["property_value"] = (
                    property_value.get("nPropValue")
                )

                final_row["property_digits"] = (
                    property_value.get("nPropDigits")
                )

                final_row["property_method"] = (
                    prop.get("method")
                )

                final_row["property_phase"] = (
                    prop.get("phase")
                )

                final_row["property_component"] = (
                    prop.get("component")
                )

                final_row["property_component_name"] = (
                    prop.get("component_name")
                )

                final_row["property_uncertainty"] = (
                    property_value
                    .get("CombinedUncertainty", {})
                    .get("nCombExpandUncertValue")
                )

                rows.append(final_row)

    return rows
