;; The first three lines of this file were inserted by DrRacket. They record metadata
;; about the language level of this file in a form that our tools can easily process.
#reader(lib "htdp-intermediate-lambda-reader.ss" "lang")((modname boolean) (read-case-sensitive #t) (teachpacks ()) (htdp-settings #(#t constructor repeating-decimal #f #t none #f () #f)))

; A ListOfBools is one of :
; - '()
; - (cons Bool ListOfBools)
; and represents a list of boolean values
(define LOB1   '())
(define LOB2.1 (list #t))
(define LOB2.2 (list #t #t))
(define LOB3.1 (list #f #t))
(define LOB3.2 (list #t #f))
(define LOB4.1 (list #f))
(define LOB4.2 (list #f #f))
(define (list-of-bools-template lob)
  (cond
    [(empty? lob) ...]
    [(cons? lob) (... (first lob) ...
                      ... (list-of-bools-template (rest lob)) ...)]))

; all-true-expanded : ListOfBools -> Bool
; Are all the values #t?
(define (all-true-expanded lob)
  (if (empty? lob)
      #t
      (and (first lob)
           (all-true-expanded (rest lob)))))
(check-expect (all-true-expanded LOB1)   #t)
(check-expect (all-true-expanded LOB2.1) #t)
(check-expect (all-true-expanded LOB2.2) #t)
(check-expect (all-true-expanded LOB3.1) #f)
(check-expect (all-true-expanded LOB3.2) #f)
(check-expect (all-true-expanded LOB4.1) #f)
(check-expect (all-true-expanded LOB4.2) #f)

; all-true : ListOfBools -> Bool
; Are all the values #t?
(define (all-true lob)
  (andmap identity lob))
(check-expect (all-true LOB1)   #t)
(check-expect (all-true LOB2.1) #t)
(check-expect (all-true LOB2.2) #t)
(check-expect (all-true LOB3.1) #f)
(check-expect (all-true LOB3.2) #f)
(check-expect (all-true LOB4.1) #f)
(check-expect (all-true LOB4.2) #f)

; one-true : ListOfBools -> Bool
; Is at least one item #t?
(define (one-true lob)
  (ormap identity lob))
(check-expect (one-true LOB1)   #f)
(check-expect (one-true LOB2.1) #t)
(check-expect (one-true LOB2.2) #t)
(check-expect (one-true LOB3.1) #t)
(check-expect (one-true LOB3.2) #t)
(check-expect (one-true LOB4.1) #f)
(check-expect (one-true LOB4.2) #f)
