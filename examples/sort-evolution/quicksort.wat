;; JEV BLOCK: sort-module-open
;; Abstract in-memory signed-i32 sorting component: insertion-sort baseline.
(module
  (memory (export "memory") 1)

;; JEV BLOCK: quicksort-swap
  (func $swap (param $left i32) (param $right i32)
    (local $value i32)
    local.get $left
    i32.load
    local.set $value
    local.get $left
    local.get $right
    i32.load
    i32.store
    local.get $right
    local.get $value
    i32.store)

;; JEV BLOCK: quicksort-partition
  (func $partition (param $offset i32) (param $low i32) (param $high i32) (result i32)
    (local $pivot i32) (local $i i32) (local $j i32)
    local.get $offset
    local.get $high
    i32.const 2
    i32.shl
    i32.add
    i32.load
    local.set $pivot
    local.get $low
    local.set $i
    local.get $low
    local.set $j
    block $scan_done
      loop $scan
        local.get $j
        local.get $high
        i32.ge_u
        br_if $scan_done
        local.get $offset
        local.get $j
        i32.const 2
        i32.shl
        i32.add
        i32.load
        local.get $pivot
        i32.le_s
        if
          local.get $offset
          local.get $i
          i32.const 2
          i32.shl
          i32.add
          local.get $offset
          local.get $j
          i32.const 2
          i32.shl
          i32.add
          call $swap
          local.get $i
          i32.const 1
          i32.add
          local.set $i
        end
        local.get $j
        i32.const 1
        i32.add
        local.set $j
        br $scan
      end
    end
    local.get $offset
    local.get $i
    i32.const 2
    i32.shl
    i32.add
    local.get $offset
    local.get $high
    i32.const 2
    i32.shl
    i32.add
    call $swap
    local.get $i)

;; JEV BLOCK: quicksort-recursive
  (func $quicksort (param $offset i32) (param $low i32) (param $high i32)
    (local $pivot_index i32)
    local.get $low
    local.get $high
    i32.lt_s
    if
      local.get $offset
      local.get $low
      local.get $high
      call $partition
      local.set $pivot_index
      local.get $offset
      local.get $low
      local.get $pivot_index
      i32.const 1
      i32.sub
      call $quicksort
      local.get $offset
      local.get $pivot_index
      i32.const 1
      i32.add
      local.get $high
      call $quicksort
    end)

;; JEV BLOCK: quicksort-export
  (func (export "sort") (param $offset i32) (param $length i32)
    local.get $length
    i32.const 1
    i32.gt_u
    if
      local.get $offset
      i32.const 0
      local.get $length
      i32.const 1
      i32.sub
      call $quicksort
    end)

;; JEV BLOCK: sort-module-close
)
