;; JEV BLOCK: checksum-module-open
;; Checksum and hash helpers using FNV-1a over linear memory.
(module
  (memory (export "memory") 1)

;; JEV BLOCK: checksum-fnv1a-and-close
  (func (export "fnv1a_32") (param $offset i32) (param $length i32) (result i32)
    (local $hash i32) (local $end i32)
    i32.const -2128831035 local.set $hash
    local.get $offset local.get $length i32.add local.set $end
    block $done
      loop $bytes
        local.get $offset local.get $end i32.ge_u br_if $done
        local.get $hash local.get $offset i32.load8_u i32.xor
        i32.const 16777619 i32.mul local.set $hash
        local.get $offset i32.const 1 i32.add local.set $offset
        br $bytes
      end
    end
    local.get $hash))
