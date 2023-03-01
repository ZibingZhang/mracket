from mracket import runner
from mracket.mutation import generator, mutator

runner.Runner.check_preconditions()

runner_ = runner.Runner(
    mutator.Mutator(
        [
            generator.ProcedureReplacement(
                {
                    "+": ["-"],
                    "-": ["+"],
                    "*": ["/"],
                    "/": ["*"],
                }
            ),
            generator.ProcedureApplicationReplacement(
                {
                    "and": ["#t", "#f"],
                    "or": ["#t", "#f"],
                    "not": ["#t", "#f"],
                    "mouse=?": ["#t", "#f"],
                }
            ),
        ]
    ),
    filename="./mracket/test/inputs/input-1.rkt",
)

runner_.run()

print(runner_.result.json())
