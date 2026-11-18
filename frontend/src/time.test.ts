import { describe, expect, it } from "vitest";
import { parseDuration, totalTime } from "./time";

describe("parseDuration", () => {
  it.each([
    ["10 min", 10, 10],
    ["1 hr", 60, 60],
    ["1 hr 15 min", 75, 75],
    ["2 hours 30 minutes", 150, 150],
    ["4 hrs", 240, 240],
    ["1h30m", 90, 90],
    ["1 day 15 min", 1455, 1455],
    ["1 hour and 5 minutes", 65, 65],
    ["1½ hours", 90, 90],
    ["1.5 hr", 90, 90],
    ["20", 20, 20],
    ["0 min", 0, 0],
    ["10-12 min", 10, 12],
    ["16 to 18 min", 16, 18],
    ["20–30 min", 20, 30],
    ["30 min - 35 min", 30, 35],
    ["1-2 hours", 60, 120],
    ["5–7 days", 7200, 10080],
    ["1 hr 25 min (includes chilling time)", 85, 85],
    ["35 min (plus cooling)", 35, 35],
  ])("%s", (text, lo, hi) => expect(parseDuration(text)).toEqual({ lo, hi }));

  it.each(["", "overnight", "about an hour", "4 servings", "12-10 min", "1-2-3 min", "until golden"])(
    "can't read %j",
    (text) => expect(parseDuration(text)).toBeNull(),
  );
});

describe("totalTime", () => {
  const times = (prep: string | null, cook: string | null, total: string | null = null) => ({
    prep_time: prep,
    cook_time: cook,
    total_time: total,
  });

  it("keeps a total time that's given", () => {
    expect(totalTime(times("10 min", "20 min", "45 min"))).toBe("45 min");
  });

  it("adds prep and cook time when the total is missing", () => {
    expect(totalTime(times("10 min", "25 min"))).toBe("35 min");
    expect(totalTime(times("15 min", "1 hr", " "))).toBe("1 hr 15 min");
    expect(totalTime(times("20 min", "2 hours (includes cooling time)"))).toBe("2 hr 20 min");
    expect(totalTime(times("1 day", "15 min"))).toBe("1 day 15 min");
    expect(totalTime(times("0 min", "45 min"))).toBe("45 min");
  });

  it("adds ranges", () => {
    expect(totalTime(times("10 min", "10-12 min"))).toBe("20–22 min");
    expect(totalTime(times("15 min", "45-60 min"))).toBe("1 hr – 1 hr 15 min");
  });

  it("shows nothing unless both times can be read", () => {
    expect(totalTime(times("10 min", null))).toBeNull();
    expect(totalTime(times(null, "20 min"))).toBeNull();
    expect(totalTime(times("10 min", "overnight"))).toBeNull();
    expect(totalTime(times("0 min", "0 min"))).toBeNull();
  });
});
