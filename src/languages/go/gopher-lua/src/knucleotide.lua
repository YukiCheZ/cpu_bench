-- KNucleotide benchmark for Lua, adapted for direct string input
-- Original from The Computer Language Benchmarks Game
-- http://benchmarksgame.alioth.debian.org/

local function kfrequency(seq, freq, k, frame)
  local sub = string.sub
  local k1 = k - 1
  for i=frame,string.len(seq)-k1,k do
    local c = sub(seq, i, i+k1)
    freq[c] = freq[c] + 1
  end
end

local function freqdefault()
  return 0
end

-- count the occurrences of a given fragment
function count(seq, frag)
  local k = string.len(frag)
  local freq = setmetatable({}, { __index = freqdefault })
  for frame=1,k do kfrequency(seq, freq, k, frame) end
end

-- compute frequency table for k-mers
function frequency(seq, k)
  local freq = setmetatable({}, { __index = freqdefault })
  for frame=1,k do kfrequency(seq, freq, k, frame) end
  local sfreq, sn = {}, 1
  for c,v in pairs(freq) do sfreq[sn] = c; sn = sn + 1 end
  table.sort(sfreq, function(a, b)
    local fa, fb = freq[a], freq[b]
    return fa == fb and a > b or fa > fb
  end)
  local sum = string.len(seq)-k+1
  for _,c in ipairs(sfreq) do
  end
end

-- new function to directly accept a DNA sequence string
function run_knucleotide(seq)
  frequency(seq, 1)
  frequency(seq, 2)
  count(seq, "GGT")
  count(seq, "GGTA")
  count(seq, "GGTATT")
  count(seq, "GGTATTTTAATT")
  count(seq, "GGTATTTTAATTTATAGT")
end
