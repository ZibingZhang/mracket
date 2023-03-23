;; The first three lines of this file were inserted by DrRacket. They record metadata
;; about the language level of this file in a form that our tools can easily process.
#reader(lib "htdp-intermediate-lambda-reader.ss" "lang")((modname distance) (read-case-sensitive #t) (teachpacks ()) (htdp-settings #(#t constructor repeating-decimal #f #t none #f () #f)))

; distance : Posn Posn -> Nat
; Compute the distance between two posns
(define (distance x y)
  (sqrt (+ (expt x 2) (expt y 2))))
(check-within (distance 1 1) (sqrt 2) 0.01)

; manhattan-distance : Posn Posn -> Nat
; Compute the Manhattan distance between two posns
(check-expect (manhattan-distance (make-posn 5 10) (make-posn 10 5)) 10)
(define (manhattan-distance a b)
  (+ (abs (- (posn-x a) (posn-x b)))
     (abs (- (posn-y a) (posn-y b)))))
