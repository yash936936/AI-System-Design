from app.schemas.schemas import MCQTemplate, MCQQuestion

_hld_questions = [
    MCQQuestion(
        question="Which of the following is NOT a primary concern in High-Level Design?",
        options=["Scalability", "Data partitioning", "Variable naming conventions", "Load balancing"],
        correct_answer="Variable naming conventions"
    )
]

_lld_questions = [
    MCQQuestion(
        question="Which pattern is best suited for decoupling services in Low-Level Design?",
        options=["Monolith", "Observer / Event-Driven", "Tight Coupling", "Synchronous HTTP only"],
        correct_answer="Observer / Event-Driven"
    )
]

def get_mcq_template(design_type: str) -> MCQTemplate:
    if design_type.lower() == "hld":
        return MCQTemplate(design_type="hld", questions=_hld_questions)
    elif design_type.lower() == "lld":
        return MCQTemplate(design_type="lld", questions=_lld_questions)
    return MCQTemplate(design_type=design_type, questions=[])