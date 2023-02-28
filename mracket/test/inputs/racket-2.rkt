#lang racket

'1 '#t 'x '() ''()
`(,1)
`(,@'(1 2 3))

(define a 1)
(define l '(1 2 3))
`(0 a ,a ,l ,@l)
