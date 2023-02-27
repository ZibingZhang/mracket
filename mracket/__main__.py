import timeit

from mracket.runner import Runner

t1 = timeit.default_timer()

Runner.check_preconditions()
runner = Runner("./mracket/test/inputs/input-1.rkt")
runner.run()

t2 = timeit.default_timer()

runner.success.pprint()

t3 = timeit.default_timer()

print((t2 - t1) / 60)
print((t3 - t2) / 60)
