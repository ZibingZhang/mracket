#lang racket

(require test-engine/racket-tests)

(check-expect 1 1)
(check-expect 2 2)
(check-expect 3 0)

(test)
