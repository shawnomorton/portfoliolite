// Site settings. Edit freely; nothing else needs to change.
window.SITE = {
  name: "Shawn Morton",
  tagline: "",
  email: "shawnomorton2002@gmail.com",            // used by the Contact link in the menu (mailto:)

  // Home gallery
  cycleMs: 420,          // milliseconds per frame on the home page (lower = faster flicker)
  shuffleHome: true,     // randomise the order on every visit
  shuffleArchive: true, // randomise the Archive wall on every visit
  pauseOnHover: false,    // hold the current frame while the mouse is over it (desktop)

  // Series pages
  openSeriesInNewTab: false,   // true = clicking a series opens it in a new browser tab
  singlePage: false,           // true = everything lives in index.html (links become #series/name); handy for hosts that only serve one page
  layout: "feed",              // "feed" (one image after another) or "grid"

  // Information page ---------------------------------------------------------
  // Each string in `bio` is one paragraph. Simple HTML is allowed (<a href="...">, <em>).
  bio: [
    "Shawn Morton is a photographer and videographer, with over ten years of experience \u2013 Las Vegas raised, Reno shaped, and now Virginia based. His visual style is built on ineffable nostalgia: warm, soft, and quietly luminous.",
    "His approach is informed by the natural world, a sense of the transcendent, and deep human connection. When not creating art, he is pursuing a Ph.D. in Genetics, Bioinformatics, and Computational Biology at Virginia Tech.",
  ],

  // Publications / clients. Plain names, or { name: "Afar", url: "https://..." } to link one.
  // Leave the list empty ([]) to hide the whole "Press:" section.
  press: [
    // "Publication name",
  ],

  // Social links. An entry with a blank url is hidden, so fill in the ones you use.
  social: [
    { label: "LinkedIn",  url: "www.linkedin.com/in/shawnomorton" },
    { label: "Instagram", url: "https://www.instagram.com/shawnomorton?dmpr=anlkN2sxdGJwaHRn&utm_source=qr" },
  ],

  // Small credit line at the bottom of the page. Blank text hides it.
  credit: { text: "", url: "" },
};
