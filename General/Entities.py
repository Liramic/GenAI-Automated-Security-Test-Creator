from dataclasses import dataclass, field
from typing import List, Dict
from General.Helpers import remove_html_tags
from General.JobClasses import JobType

@dataclass
class CounterMeasure:
    name : str
    description : str
    ref: str
    library: str = field(default=None)
    risk: int = field(default= -1)
    udts: Dict[str, str] = field(default=None)
    current_test_steps: List[str] = field(default=None)
    genai_test : dict = field(default=None)
    df_index: int = field(default=None)
    genai_cm_name: str = field(default=None)
    genai_cm_desc: str = field(default=None)
    genai_cm_code_test: str = field(default=None)

    def should_update(self, job_type):
        if ( job_type == JobType.CREATE_TEST ):
            return not self.genai_test
        elif ( job_type == JobType.EXPLAIN_COUNTERMEASURE ):
            return not self.genai_cm_name
        elif ( job_type == JobType.CREATE_CODE_TEST ):
            return not self.genai_cm_code_test
        return False

    def get_description(self):
        return f"Countermeasure name: {self.name}\nCountermeasure ref: {self.ref}\nCountermeasure description: {remove_html_tags(self.description)}"
    
    def export_to_dict(self, isMinimal = False): 
        if ( isMinimal ):
            return {
                "ref": self.ref,
                "genai_test": self.genai_test,
                "cellebrtie_cm_name": self.genai_cm_name,
                "genai_cm_desc": self.genai_cm_desc,
                "genai_cm_code_test": self.genai_cm_code_test
            }

        return {
            "name": self.name,
            "ref": self.ref,
            "description": self.description,
            "risk": self.risk,
            "udts": self.udts,
            "current_test_steps": self.current_test_steps,
            "genai_test": self.genai_test,
            "genai_cm_name": self.genai_cm_name,
            "genai_cm_desc": self.genai_cm_desc,
            "genai_cm_code_test": self.genai_cm_code_test
        }
    
    @staticmethod
    def load_from_dict(data: Dict, isMinimal = False):
        if ( isMinimal ):
            return CounterMeasure(
                ref = data["ref"],
                genai_test = data["genai_test"],
                genai_cm_name = data.get("genai_cm_name", ""),
                genai_cm_desc = data.get("genai_cm_desc", ""),
                genai_cm_code_test= data.get("genai_cm_code_test", "")
            )

        return CounterMeasure(
            name = data["name"],
            description = data["description"],
            ref = data["ref"],
            genai_test = data["genai_test"],
            current_test_steps = data["current_test_steps"],
            risk = data.get("risk", -1),
            udts = data.get("udts", {}),
            genai_cm_name = data.get("genai_cm_name", ""),
            genai_cm_desc = data.get("genai_cm_desc", ""),
            genai_cm_code_test = data.get("genai_cm_code_test", "")
        )
    
    
@dataclass
class Threat:
    name : str
    ref : str
    desc: str
    counterMeasures : Dict[str, CounterMeasure]

    def get_description(self):
        return f"Threat name: {self.name}\nThreat ref: {self.ref}\nThreat description: {self.desc}"

    def __str__(self):
        return f"Threat name: {self.name}, ref: {self.ref}, desc: {self.desc}, counterMeasures: {self.counterMeasures}"
    
    def export_to_dict(self, isMinimal = False):
        if ( isMinimal ):
            return {
                "ref": self.ref,
                "counterMeasures": {counterMeasure.ref: counterMeasure.export_to_dict(isMinimal=True) for counterMeasure in self.counterMeasures.values()}
            }
        
        return {
            "name": self.name,
            "ref": self.ref,
            "desc": self.desc,
            "counterMeasures": {counterMeasure.ref: counterMeasure.export_to_dict() for counterMeasure in self.counterMeasures.values()}
        }
    
    @staticmethod
    def load_threat_from_dict(data: Dict, isMinimal = False):
        if ( isMinimal ):
            return Threat(
                ref = data["ref"],
                counterMeasures = {counterMeasure["ref"]: CounterMeasure.load_from_dict(counterMeasure, isMinimal=True) for counterMeasure in data["counterMeasures"].values()}
            )

        return Threat(
            name = data["name"],
            ref = data["ref"],
            desc = data["desc"],
            counterMeasures = {counterMeasure["ref"]: CounterMeasure.load_from_dict(counterMeasure) for counterMeasure in data["counterMeasures"].values()}
        )



@dataclass
class Component:
    name : str
    ref: str
    threats : Dict[str,Threat]

    def get_description(self):
        return f"Component name: {self.name}"
    
    def export_component_to_dict(self, isMinimal = False):
        if (isMinimal):
            return {
                "threats": {threat.ref : threat.export_to_dict(isMinimal) for threat in self.threats.values()}
            }

        return {
            "name": self.name,
            "ref": self.ref,
            "threats": {threat.ref : threat.export_to_dict(isMinimal) for threat in self.threats.values()}
        }
    
    @staticmethod
    def load_component_from_dict(data: Dict, isMinimal = False):
        if ( isMinimal ):
            return Component(
                threats = {threat["ref"]: Threat.load_threat_from_dict(threat, isMinimal=True) for threat in data["threats"].values()},
            )

        return Component(
            name = data["name"],
            ref = data["ref"],
            threats = {threat["ref"]: Threat.load_threat_from_dict(threat) for threat in data["threats"].values()}
        )


# component conversion functions #

def load_components_from_dict(data: Dict, isMinimal = False):
    return {component_ref: Component.load_component_from_dict(component, isMinimal) for component_ref, component in data.items()}

def export_components_to_dict(components: List[Component], isMinimal = False):
    return {component.ref: component.export_component_to_dict(isMinimal) for component in components}

def export_components_to_dict(components: Dict[str, Component], isMinimal = False):
    return {component_ref: component.export_component_to_dict(isMinimal) for component_ref, component in components.items()}
