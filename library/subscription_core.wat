;; JEV BLOCK: subscription-module-open
;; Generic subscription and recurring-billing arithmetic.
(module

;; JEV BLOCK: subscription-monthly-cents
  (func (export "monthly_cents") (param $amount i64) (param $period i32) (result i64)
    local.get $amount i64.const 0 i64.lt_s
    if (result i64)
      i64.const -1
    else
      local.get $period i32.const 0 i32.eq
      if (result i64)
        local.get $amount i64.const 52 i64.mul i64.const 12 i64.div_s
      else
        local.get $period i32.const 1 i32.eq
        if (result i64)
          local.get $amount
        else
          local.get $period i32.const 2 i32.eq
          if (result i64)
            local.get $amount i64.const 3 i64.div_s
          else
            local.get $period i32.const 3 i32.eq
            if (result i64)
              local.get $amount i64.const 12 i64.div_s
            else
              i64.const -2
            end
          end
        end
      end
    end)

;; JEV BLOCK: subscription-due-and-close
  (func (export "is_due") (param $next_day i64) (param $through_day i64) (param $active i32) (result i32)
    local.get $active i32.eqz
    if (result i32)
      i32.const 0
    else
      local.get $next_day local.get $through_day i64.le_s
    end))
