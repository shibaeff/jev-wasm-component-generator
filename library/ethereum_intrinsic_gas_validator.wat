;; JEV BLOCK: ethereum-intrinsic-gas-module-open
;; Pure ordered validation over already-calculated Ethereum transaction gas values.
(module

;; JEV BLOCK: ethereum-intrinsic-gas-ordered-validation
  (func (export "validate_intrinsic_gas")
    (param $gas_limit i64)
    (param $initial_total i64)
    (param $floor_gas i64)
    (param $initial_regular i64)
    (param $regular_cap i64)
    (result i32)
    local.get $gas_limit
    local.get $initial_total
    i64.lt_u
    if
      i32.const 1
      return
    end
    local.get $gas_limit
    local.get $floor_gas
    i64.lt_u
    if
      i32.const 2
      return
    end
    local.get $regular_cap
    i64.eqz
    if
    else
      local.get $initial_regular
      local.get $floor_gas
      i64.gt_u
      if (result i64)
        local.get $initial_regular
      else
        local.get $floor_gas
      end
      local.get $regular_cap
      i64.gt_u
      if
        i32.const 3
        return
      end
    end
    i32.const 0)

;; JEV BLOCK: ethereum-intrinsic-gas-module-close
)
