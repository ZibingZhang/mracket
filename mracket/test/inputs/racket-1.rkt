#lang racket

(define CONST 1)
CONST

(define (x a) (+ a 3))
(x 1)

(define (y a)
  (cond
    [a 1]
    [else 2]))
(y #t)
(y #f)

(define (z a)
  (if a 1 2))
(z #t)
(z #f)

(define-struct posn [x y])
(make-posn 0 1)
