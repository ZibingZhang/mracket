;; The first three lines of this file were inserted by DrRacket. They record metadata
;; about the language level of this file in a form that our tools can easily process.
#reader(lib "htdp-intermediate-lambda-reader.ss" "lang")((modname factorial) (read-case-sensitive #t) (teachpacks ()) (htdp-settings #(#t constructor repeating-decimal #f #t none #f () #f)))

; fact : Nat -> Nat
; Compute the factorial of a number
(define (fact n)
  (if (zero? n)
      1
      (* n (fact (sub1 n)))))
(check-expect (fact 0) 1)
(check-expect (fact 1) 1)
(check-expect (fact 5) 120)
(check-expect (fact 10) 3628800)

; fact-acc : Nat -> Nat
; Compute the factorial of a number
(define (fact-acc n)
  (fact-acc-helper n 1))
(define (fact-acc-helper n acc)
  (if (zero? n)
      acc
      (fact-acc-helper (sub1 n) (* n acc))))
(check-expect (fact-acc 0) 1)
(check-expect (fact-acc 1) 1)
(check-expect (fact-acc 5) 120)
(check-expect (fact-acc 10) 3628800)
