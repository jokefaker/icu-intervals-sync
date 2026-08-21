const raw = icu.activity.StravaSegmentsJson

let payload = { aid: "", segments: [] }
try {
  if (typeof raw === "string" && raw.trim()) payload = JSON.parse(raw)
} catch (e) {
  payload = { aid: "", segments: [] }
}

const rows = Array.isArray(payload.segments) ? payload.segments : []
const streamData = name => {
  const stream = icu.streams.get(name)
  return stream && Array.isArray(stream.data) ? stream.data : []
}

const watts = streamData("watts")
const heartrate = streamData("heartrate")
const cadence = streamData("cadence")
const torque = streamData("torque")
const altitude = streamData("altitude")
const distance = streamData("distance")
const time = streamData("time")

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

const range = (values, start, end) => values.slice(start, Math.min(end, values.length))
const mean = (values, start, end, positiveOnly = false) => {
  const selected = range(values, start, end).filter(value =>
    Number.isFinite(value) && (!positiveOnly || value > 0))
  return selected.length ? selected.reduce((sum, value) => sum + value, 0) / selected.length : null
}
const maximum = (values, start, end) => {
  const selected = range(values, start, end).filter(value => Number.isFinite(value) && value > 0)
  return selected.length ? Math.max(...selected) : null
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
  const rolling = []
  for (let i = start; i < end && i < watts.length; i++) {
    const window = watts.slice(Math.max(0, i - 29), i + 1)
      .filter(value => Number.isFinite(value))
    if (!window.length) continue
    rolling.push(window.reduce((sum, value) => sum + value, 0) / window.length)
  }
  if (!rolling.length) return null
  return Math.pow(rolling.reduce((sum, value) => sum + Math.pow(value, 4), 0) / rolling.length, 0.25)
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

const dark = Boolean(icu.darkMode)
const normalRows = dark ? ["#191B1F", "#202329"] : ["#FFFFFF", "#F6F7F9"]
const starredRow = dark ? "#3A2A1F" : "#FFF1E8"
const textColor = dark ? "#E7E9EC" : "#25282D"
const mutedColor = dark ? "#A8ADB5" : "#6D737C"
const gridColor = dark ? "#30343A" : "#E8EAED"
const headerColor = dark ? "#111317" : "#26292E"
const linkColor = dark ? "#FF7A45" : "#D83B01"
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
const headerHeight = 40 / 31
const totalHeight = rows.length + headerHeight
const columnStarts = []
columnWidths.reduce((position, width) => {
  columnStarts.push(position)
  return position + width
}, 0)

const shapes = []
const annotations = []
const annotationFont = { family: "Arial, Microsoft YaHei, sans-serif", size: 11, color: textColor }

shapes.push({
  type: "rect",
  xref: "x",
  yref: "y",
  x0: 0,
  x1: totalWidth,
  y0: rows.length,
  y1: totalHeight,
  line: { width: 0 },
  fillcolor: headerColor,
  layer: "below"
})

rows.forEach((row, rowIndex) => {
  const y0 = rows.length - rowIndex - 1
  const y1 = y0 + 1
  shapes.push({
    type: "rect",
    xref: "x",
    yref: "y",
    x0: 0,
    x1: totalWidth,
    y0,
    y1,
    line: { width: 0 },
    fillcolor: row.f ? starredRow : normalRows[rowIndex % 2],
    layer: "below"
  })
})

for (let boundary = 0; boundary <= columnWidths.length; boundary++) {
  const x = boundary === columnWidths.length
    ? totalWidth
    : columnStarts[boundary]
  shapes.push({
    type: "line",
    xref: "x",
    yref: "y",
    x0: x,
    x1: x,
    y0: 0,
    y1: totalHeight,
    line: { color: gridColor, width: 1 },
    layer: "above"
  })
}
for (let rowBoundary = 0; rowBoundary <= rows.length; rowBoundary++) {
  shapes.push({
    type: "line",
    xref: "x",
    yref: "y",
    x0: 0,
    x1: totalWidth,
    y0: rowBoundary,
    y1: rowBoundary,
    line: { color: gridColor, width: 1 },
    layer: "above"
  })
}
shapes.push({
  type: "line",
  xref: "x",
  yref: "y",
  x0: 0,
  x1: totalWidth,
  y0: totalHeight,
  y1: totalHeight,
  line: { color: gridColor, width: 1 },
  layer: "above"
})

headers.forEach((header, columnIndex) => {
  const isName = columnIndex === 0
  annotations.push({
    xref: "x",
    yref: "y",
    x: isName
      ? columnStarts[columnIndex] + 9
      : columnStarts[columnIndex] + columnWidths[columnIndex] / 2,
    y: rows.length + headerHeight / 2,
    text: header,
    showarrow: false,
    xanchor: isName ? "left" : "center",
    yanchor: "middle",
    align: isName ? "left" : "center",
    font: { family: annotationFont.family, size: 11, color: "#FFFFFF" }
  })
})

rows.forEach((row, rowIndex) => {
  const y = rows.length - rowIndex - 0.5
  values.forEach((columnValues, columnIndex) => {
    const isName = columnIndex === 0
    const isZone = columnIndex === 9
    const xanchor = isName ? "left" : isZone ? "center" : "right"
    const x = isName
      ? columnStarts[columnIndex] + 9
      : isZone
        ? columnStarts[columnIndex] + columnWidths[columnIndex] / 2
        : columnStarts[columnIndex] + columnWidths[columnIndex] - 8
    const value = String(columnValues[rowIndex])
    const segmentId = segmentIds[rowIndex]
    const text = isName && segmentId
      ? `<a href="https://www.strava.com/segments/${segmentId}" target="_blank">${value}</a>`
      : value

    annotations.push({
      xref: "x",
      yref: "y",
      x,
      y,
      text,
      showarrow: false,
      xanchor,
      yanchor: "middle",
      align: isName ? "left" : isZone ? "center" : "right",
      font: isName && segmentId
        ? { ...annotationFont, color: linkColor }
        : annotationFont
    })
  })
})

const starredCount = rows.filter(row => row.f).length
chart = rows.length ? {
  data: [{
    type: "scatter",
    x: [0, totalWidth],
    y: [0, totalHeight],
    mode: "markers",
    marker: { opacity: 0, size: 1 },
    hoverinfo: "skip",
    showlegend: false
  }],
  layout: {
    title: {
      text: `<b>Strava 路段</b>  <span style="font-size:12px;color:${mutedColor}">${rows.length} 个路段 · ${starredCount} 个收藏</span>`,
      x: 0.01,
      xanchor: "left",
      font: { color: textColor, size: 16 }
    },
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
    shapes,
    annotations,
    hovermode: false,
    showlegend: false,
    plot_bgcolor: dark ? "#191B1F" : "#FFFFFF",
    paper_bgcolor: dark ? "#191B1F" : "#FFFFFF",
    margin: { l: 0, r: 0, t: 48, b: 0 },
    height: Math.max(170, 90 + rows.length * 31)
  }
} : null
