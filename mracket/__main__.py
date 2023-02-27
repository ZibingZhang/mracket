from mracket import runner
from mracket.mutation import generator, mutator

runner.Runner.check_preconditions()

runner_ = runner.Runner(
    "./mracket/test/inputs/input-1.rkt", mutator.Mutator([generator.ProcedureReplacement({"+": {"-", "*"}})])
)

runner_.run()

runner_.success.pprint()
