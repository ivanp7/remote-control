;;;; remote-control.asd

(asdf:defsystem #:remote-control
  :description "Remote computer handling utility"
  :author "Ivan Podmazov <ivanpzv8@gmail.com>"
  :license  "MIT"
  :depends-on (#:alexandria)
  :components ((:static-file "README.md")
               (:static-file "LICENSE")
               (:static-file "roswell/remote.ros")))

