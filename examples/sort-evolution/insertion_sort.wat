;; JEV BLOCK: sort-module-open
;; Abstract in-memory signed-i32 sorting component: insertion-sort baseline.
(module
  (memory (export "memory") 1)

;; JEV BLOCK: insertion-sort-helper
  (func $insertion_sort (param $offset i32) (param $length i32)
    (local $i i32) (local $j i32) (local $key i32) (local $previous i32)
    i32.const 1
    local.set $i
    block $done
      loop $outer
        local.get $i
        local.get $length
        i32.ge_u
        br_if $done
        local.get $offset
        local.get $i
        i32.const 2
        i32.shl
        i32.add
        i32.load
        local.set $key
        local.get $i
        local.set $j
        block $placed
          loop $shift
            local.get $j
            i32.eqz
            br_if $placed
            local.get $offset
            local.get $j
            i32.const 1
            i32.sub
            i32.const 2
            i32.shl
            i32.add
            i32.load
            local.tee $previous
            local.get $key
            i32.le_s
            br_if $placed
            local.get $offset
            local.get $j
            i32.const 2
            i32.shl
            i32.add
            local.get $previous
            i32.store
            local.get $j
            i32.const 1
            i32.sub
            local.set $j
            br $shift
          end
        end
        local.get $offset
        local.get $j
        i32.const 2
        i32.shl
        i32.add
        local.get $key
        i32.store
        local.get $i
        i32.const 1
        i32.add
        local.set $i
        br $outer
      end
    end)

;; JEV BLOCK: insertion-sort-export
  (func (export "sort") (param $offset i32) (param $length i32)
    local.get $offset
    local.get $length
    call $insertion_sort)

;; JEV BLOCK: sort-module-close
)
