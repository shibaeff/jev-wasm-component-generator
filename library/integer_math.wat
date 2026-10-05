;; JEV BLOCK: integer-math-module-open
;; Small integer component library.
(module

;; JEV BLOCK: integer-math-clamp
  (func (export "clamp_i32") (param $value i32) (param $low i32) (param $high i32) (result i32)
    local.get $value local.get $low i32.lt_s
    if (result i32)
      local.get $low
    else
      local.get $value local.get $high i32.gt_s
      if (result i32) local.get $high else local.get $value end
    end)

;; JEV BLOCK: integer-math-gcd-and-close
  (func (export "gcd_u32") (param $a i32) (param $b i32) (result i32)
    (local $remainder i32)
    block $done
      loop $again
        local.get $b i32.eqz br_if $done
        local.get $a local.get $b i32.rem_u local.set $remainder
        local.get $b local.set $a
        local.get $remainder local.set $b
        br $again
      end
    end
    local.get $a))
