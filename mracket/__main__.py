from mracket import runner
from mracket.mutation import generator, mutator

runner.Runner.check_preconditions()

runner_ = runner.Runner(
    mutator.Mutator([generator.ProcedureReplacement({"+": ["-", "*"]})]), filename="./mracket/test/inputs/input-1.rkt"
)

runner_.run()

runner_.success.pprint()
