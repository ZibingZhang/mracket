; racket mracket/reader/lexer.rkt examples/factorial.rkt

#lang racket
(require racket/cmdline)

(define filename
  (command-line
   #:program "lexer"
   #:args (filename)
   filename))

(define input-file (open-input-file filename))
(define (display-syntax-from-file)
  (let ([stx (read-syntax filename input-file)])
    (if (eof-object? stx)
        (void)
        (begin
          (display-syntax stx)
          (display-syntax-from-file)))))

(define (display-syntax stx)
  (let ([sub-stxs (syntax->list stx)])
    (if sub-stxs
        (let ([pos (syntax-position stx)]
              [len (syntax-span stx)])
          (displayln (~a pos " ("))
          (map display-syntax sub-stxs)
          (displayln (~a (+ pos len) " )")))
        (displayln (~a (syntax-position stx) " " (syntax->datum stx))))))

(display-syntax-from-file)
