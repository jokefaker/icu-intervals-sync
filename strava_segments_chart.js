{
const raw = icu.activity.StravaSegmentsJson

let payload = { aid: "", segments: [] }
try {
  if (typeof raw === "string" && raw.trim()) payload = JSON.parse(raw)
} catch (e) {
  payload = { aid: "", segments: [] }
}

const rows = Array.isArray(payload.segments) ? payload.segments : []
const watts = icu.streams.watts || []
const heartrate = icu.streams.heartrate || []
const cadence = icu.streams.cadence || []
const torque = icu.streams.torque || []
const altitude = icu.streams.altitude || []
const distance = icu.streams.distance || []
const time = icu.streams.time || []

const digits = value => /^\d+$/.test(String(value || "")) ? String(value) : ""
const escapeHtml = value => String(value || "")
  .replace(/&/g, "&amp;")
  .replace(/</g, "&lt;")
  .replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;")
const compactName = value => {
  const characters = Array.from(String(value || "未命名路段"))
  const display = characters.length > 24
    ? `${characters.slice(0, 23).join("")}...`
    : characters.join("")
  return escapeHtml(display)
}

const mean = (values, start, end, positiveOnly = false) => {
  let sum = 0
  let count = 0
  const finish = Math.min(end, values.length)
  for (let i = Math.max(0, start); i < finish; i++) {
    const value = values[i]
    if (!Number.isFinite(value) || (positiveOnly && value <= 0)) continue
    sum += value
    count++
  }
  return count ? sum / count : null
}
const maximum = (values, start, end) => {
  let result = null
  const finish = Math.min(end, values.length)
  for (let i = Math.max(0, start); i < finish; i++) {
    const value = values[i]
    if (Number.isFinite(value) && value > 0 && (result === null || value > result)) {
      result = value
    }
  }
  return result
}
const round = (value, fractionDigits = 0, suffix = "") =>
  Number.isFinite(value) ? `${value.toFixed(fractionDigits)}${suffix}` : "-"
const formatDuration = value => {
  if (!Number.isFinite(value) || value < 0) return "-"
  const total = Math.round(value)
  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const seconds = total % 60
  const hourText = hours > 0 ? `${hours}h` : ""
  const minuteText = minutes > 0 || hours > 0 ? `${minutes}m` : ""
  return `${hourText}${minuteText}${seconds}s`
}

const normalizedPower = (start, end) => {
  if (!watts.length || end <= start) return null
  let rollingSum = 0
  let rollingCount = 0
  let fourthPowerSum = 0
  let fourthPowerCount = 0
  const first = Math.max(0, start - 29)
  const finish = Math.min(end, watts.length)
  for (let i = first; i < finish; i++) {
    const value = watts[i]
    if (Number.isFinite(value)) {
      rollingSum += value
      rollingCount++
    }
    if (i >= start && rollingCount) {
      fourthPowerSum += Math.pow(rollingSum / rollingCount, 4)
      fourthPowerCount++
    }
    const expired = i - 29
    if (expired >= first && Number.isFinite(watts[expired])) {
      rollingSum -= watts[expired]
      rollingCount--
    }
  }
  return fourthPowerCount
    ? Math.pow(fourthPowerSum / fourthPowerCount, 0.25)
    : null
}

const elapsedSeconds = (start, end) => {
  if (!time.length || start >= time.length) return Math.max(0, end - start)
  if (end < time.length) return Math.max(0, time[end] - time[start])
  return Math.max(0, time[time.length - 1] - time[start] + 1)
}
const distanceMeters = (start, end) => {
  if (!distance.length || start >= distance.length) return null
  const finish = end < distance.length ? end : distance.length - 1
  return Math.max(0, distance[finish] - distance[start])
}

const averageGradient = (start, end, meters) => {
  if (!altitude.length || !meters || start >= altitude.length) return null
  const finish = end < altitude.length ? end : altitude.length - 1
  return (altitude[finish] - altitude[start]) / meters * 100
}

const vam = (start, end, seconds) => {
  if (!altitude.length || seconds <= 0) return null
  let gain = 0
  const finish = Math.min(end, altitude.length - 1)
  for (let i = Math.max(start + 1, 1); i <= finish; i++) {
    const delta = altitude[i] - altitude[i - 1]
    if (Number.isFinite(delta) && delta > 0) gain += delta
  }
  return gain > 0 ? gain / seconds * 3600 : null
}

const decoupling = (start, end) => {
  if (!watts.length || !heartrate.length || end - start < 2) return null
  const middle = Math.floor((start + end) / 2)
  const firstPower = mean(watts, start, middle)
  const secondPower = mean(watts, middle, end)
  const firstHr = mean(heartrate, start, middle, true)
  const secondHr = mean(heartrate, middle, end, true)
  if (![firstPower, secondPower, firstHr, secondHr].every(value => Number.isFinite(value) && value > 0)) return null
  const firstRatio = firstPower / firstHr
  const secondRatio = secondPower / secondHr
  return (1 - secondRatio / firstRatio) * 100
}

const zoneFor = averageWatts => {
  const ftp = Number(icu.activity.icu_ftp)
  const boundaries = Array.isArray(icu.activity.icu_power_zones) ? icu.activity.icu_power_zones : []
  if (!Number.isFinite(averageWatts) || !Number.isFinite(ftp) || ftp <= 0 || !boundaries.length) return "-"
  const percent = averageWatts / ftp * 100
  const index = boundaries.findIndex(boundary => percent <= boundary)
  return `Z${index < 0 ? boundaries.length : index + 1}`
}

const names = []
const segmentIds = []
const elapsedTimes = []
const averagePowers = []
const normalizedPowers = []
const averageHrs = []
const maxHrs = []
const averageCadences = []
const averageGradients = []
const intensities = []
const zones = []
const averageTorques = []
const decouplings = []
const vams = []
const distances = []
const averageSpeeds = []
let starredCount = 0

const dark = Boolean(icu.darkMode)
const normalRows = dark ? ["#191B1F", "#202329"] : ["#FFFFFF", "#F6F7F9"]
const starredRow = dark ? "#3A2A1F" : "#FFF1E8"
const textColor = dark ? "#E7E9EC" : "#25282D"
const mutedColor = dark ? "#A8ADB5" : "#6D737C"
const gridColor = dark ? "#30343A" : "#E8EAED"
const headerColor = dark ? "#111317" : "#26292E"
const linkColor = dark ? "#66B2FF" : "#1A73E8"
const ftp = Number(icu.activity.icu_ftp)

rows.forEach(row => {
  const start = Number.isInteger(row.a) ? row.a : 0
  const end = Number.isInteger(row.b) ? row.b : start
  const avgPower = mean(watts, start, end)
  const np = normalizedPower(start, end)
  const seconds = elapsedSeconds(start, end)
  const meters = distanceMeters(start, end)
  const avgSpeed = Number.isFinite(meters) && seconds > 0 ? meters / seconds * 3.6 : null
  const intensity = Number.isFinite(avgPower) && Number.isFinite(ftp) && ftp > 0 ? avgPower / ftp * 100 : null
  const gradient = averageGradient(start, end, meters)
  const avgHr = mean(heartrate, start, end, true)
  if (row.f) starredCount++

  names.push(`${row.f ? "★  " : ""}${compactName(row.n)}`)
  segmentIds.push(digits(row.s))
  elapsedTimes.push(formatDuration(seconds))
  averagePowers.push(round(avgPower, 0, " W"))
  normalizedPowers.push(round(np, 0, " W"))
  averageHrs.push(Number.isFinite(avgHr) ? `${Math.floor(avgHr)} bpm` : "-")
  maxHrs.push(round(maximum(heartrate, start, end), 0, " bpm"))
  averageCadences.push(round(mean(cadence, start, end), 0, " rpm"))
  averageGradients.push(round(gradient, 1, "%"))
  intensities.push(Number.isFinite(intensity) ? `${Math.floor(intensity)}%` : "-")
  zones.push(zoneFor(avgPower))
  averageTorques.push(round(mean(torque, start, end, true), 1, " Nm"))
  decouplings.push(round(decoupling(start, end), 1, "%"))
  vams.push(Number.isFinite(gradient) && gradient > 0 ? round(vam(start, end, seconds), 0, " m/h") : "-")
  distances.push(Number.isFinite(meters) ? `${(meters / 1000).toFixed(2)} km` : "-")
  averageSpeeds.push(round(avgSpeed, 1, " km/h"))
})

const headers = [
  "路段",
  "历时",
  "平均功率",
  "标准化功率",
  "平均心率",
  "最大心率",
  "平均踏频",
  "平均坡度",
  "强度",
  "区间",
  "平均扭矩",
  "解耦",
  "VAM",
  "距离",
  "平均速度"
]
const values = [
  names,
  elapsedTimes,
  averagePowers,
  normalizedPowers,
  averageHrs,
  maxHrs,
  averageCadences,
  averageGradients,
  intensities,
  zones,
  averageTorques,
  decouplings,
  vams,
  distances,
  averageSpeeds
]
const columnWidths = [270, 62, 68, 76, 68, 68, 68, 68, 58, 48, 72, 62, 58, 66, 72]
const totalWidth = columnWidths.reduce((sum, width) => sum + width, 0)
const columnEdges = [0]
const columnCenters = []
let columnOffset = 0
columnWidths.forEach(width => {
  columnCenters.push(columnOffset + width / 2)
  columnOffset += width
  columnEdges.push(columnOffset)
})

const headerHeight = 40 / 31
const totalHeight = rows.length + headerHeight
const rowEdges = Array.from({ length: rows.length + 1 }, (_, index) => index)
rowEdges.push(totalHeight)
const backgroundRows = []
for (let rowIndex = rows.length - 1; rowIndex >= 0; rowIndex--) {
  const colorCode = rows[rowIndex].f ? 2 : rowIndex % 2
  backgroundRows.push(headers.map(() => colorCode))
}
backgroundRows.push(headers.map(() => 3))

const headerX = []
const headerY = []
const headerText = []
const headerPositions = []
headers.forEach((header, columnIndex) => {
  const isName = columnIndex === 0
  headerX.push(isName ? columnEdges[columnIndex] + 8 : columnCenters[columnIndex])
  headerY.push(rows.length + headerHeight / 2)
  headerText.push(`<b>${header}</b>`)
  headerPositions.push(isName ? "middle right" : "middle center")
})

const bodyX = []
const bodyY = []
const bodyText = []
const bodyPositions = []
rows.forEach((row, rowIndex) => {
  values.forEach((columnValues, columnIndex) => {
    const isName = columnIndex === 0
    const isCentered = columnIndex === 9
    const segmentId = segmentIds[rowIndex]
    const value = String(columnValues[rowIndex])
    bodyX.push(isName
      ? columnEdges[columnIndex] + 8
      : isCentered
        ? columnCenters[columnIndex]
        : columnEdges[columnIndex + 1] - 8)
    bodyY.push(rows.length - rowIndex - 0.5)
    bodyText.push(isName && segmentId
      ? `<a href="https://www.strava.com/segments/${segmentId}" target="_blank"><span style="color:${linkColor}">${value}</span></a>`
      : value)
    bodyPositions.push(isName
      ? "middle right"
      : isCentered
        ? "middle center"
        : "middle left")
  })
})

const colorScale = [
  [0, normalRows[0]],
  [0.1666, normalRows[0]],
  [0.1667, normalRows[1]],
  [0.4999, normalRows[1]],
  [0.5, starredRow],
  [0.8332, starredRow],
  [0.8333, headerColor],
  [1, headerColor]
]
const chartHeight = Math.max(170, 88 + rows.length * 31)

chart = rows.length ? {
  data: [
    {
      type: "heatmap",
      x: columnEdges,
      y: rowEdges,
      z: backgroundRows,
      zmin: 0,
      zmax: 3,
      colorscale: colorScale,
      showscale: false,
      hoverinfo: "skip",
      xgap: 1,
      ygap: 1
    },
    {
      type: "scatter",
      mode: "text",
      x: headerX,
      y: headerY,
      text: headerText,
      textposition: headerPositions,
      textfont: { family: "Arial, Microsoft YaHei, sans-serif", size: 11, color: "#FFFFFF" },
      cliponaxis: false,
      hoverinfo: "skip",
      showlegend: false
    },
    {
      type: "scatter",
      mode: "text",
      x: bodyX,
      y: bodyY,
      text: bodyText,
      textposition: bodyPositions,
      textfont: { family: "Arial, Microsoft YaHei, sans-serif", size: 11, color: textColor },
      cliponaxis: false,
      hoverinfo: "skip",
      showlegend: false
    }
  ],
  layout: {
    title: {
      text: `<b>Strava 路段</b>  <span style="font-size:12px;color:${mutedColor}">${rows.length} 个路段 · ${starredCount} 个收藏</span>`,
      x: 0.01,
      xanchor: "left",
      font: { color: textColor, size: 16 }
    },
    hovermode: false,
    showlegend: false,
    xaxis: {
      range: [0, totalWidth],
      visible: false,
      fixedrange: true
    },
    yaxis: {
      range: [0, totalHeight],
      visible: false,
      fixedrange: true
    },
    plot_bgcolor: dark ? "#191B1F" : "#FFFFFF",
    paper_bgcolor: dark ? "#191B1F" : "#FFFFFF",
    margin: { l: 0, r: 0, t: 48, b: 0 },
    height: chartHeight
  }
} : null
}
