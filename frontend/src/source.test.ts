import { describe, expect, it } from "vitest";
import { recipeSource } from "./source";

describe("recipeSource", () => {
  it("shows a source name without a link", () => {
    expect(recipeSource("The Joy of Cooking", null)).toEqual({ label: "The Joy of Cooking", href: null });
    expect(recipeSource("Grandma", "  ")).toEqual({ label: "Grandma", href: null });
  });

  it("links the name to the source", () => {
    expect(recipeSource("Example Kitchen", "https://example.com/soup")).toEqual({
      label: "Example Kitchen",
      href: "https://example.com/soup",
    });
  });

  it("falls back to the site's name", () => {
    expect(recipeSource(null, "https://www.example.com/soup")).toEqual({
      label: "www.example.com",
      href: "https://www.example.com/soup",
    });
    expect(recipeSource("  ", "http://example.com")?.label).toBe("example.com");
  });

  it("adds a missing scheme to a bare domain", () => {
    expect(recipeSource(null, "example.com/soup")).toEqual({
      label: "example.com",
      href: "https://example.com/soup",
    });
  });

  it("shows other text without linking it", () => {
    expect(recipeSource(null, "grandma's recipe box")).toEqual({ label: "grandma's recipe box", href: null });
    expect(recipeSource(null, "grandma")).toEqual({ label: "grandma", href: null });
    expect(recipeSource("Evil", "javascript:alert(1)")).toEqual({ label: "Evil", href: null });
  });

  it("is empty when there's nothing to show", () => {
    expect(recipeSource(null, null)).toBeNull();
    expect(recipeSource("", " ")).toBeNull();
  });
});
