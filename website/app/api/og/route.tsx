import { ImageResponse } from "next/og";

// Decryption helper
function decryptLanyardData(
  encrypted: string
): { username: string; variant: "dark" | "light" } | null {
  const OBFUSCATION_KEY = "v0gdl";

  if (!encrypted) return null;
  try {
    let base64 = encrypted.replace(/-/g, "+").replace(/_/g, "/");
    const padding = (4 - (base64.length % 4)) % 4;
    base64 += "=".repeat(padding);

    const binary = atob(base64);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    const decoded = new TextDecoder().decode(bytes);

    if (decoded.startsWith(`${OBFUSCATION_KEY}:`)) {
      const withoutKey = decoded.slice(OBFUSCATION_KEY.length + 1);
      const colonIndex = withoutKey.indexOf(":");
      if (colonIndex === -1) return null;

      const variant = withoutKey.slice(0, colonIndex) as "dark" | "light";
      const username = withoutKey.slice(colonIndex + 1);

      if (variant !== "dark" && variant !== "light") return null;

      return { username, variant };
    }
    return null;
  } catch {
    return null;
  }
}

async function loadGoogleFont (font: string, text: string) {
    const url = `https://fonts.googleapis.com/css2?family=${font}&text=${encodeURIComponent(text)}`
    const css = await (await fetch(url)).text()
    const resource = css.match(/src: url\((.+)\) format\('(opentype|truetype)'\)/)

    if (resource) {
        const response = await fetch(resource[1])

        if (response.status == 200) {
            return await response.arrayBuffer()
        }
    }

    throw new Error('failed to load font data')
}

export async function GET(request: Request) {
  try {

      // Event details - you can edit these
      const EVENT_CITY = "cloud / vps";
      const EVENT_DATE = "active engine";
      const TITLE = 'Arcen Agent'

    const { searchParams } = new URL(request.url);
    const encrypted = searchParams.get("u");
    const format = searchParams.get("format") || "og"; // og, twitter, linkedin, square

    const data = encrypted ? decryptLanyardData(encrypted) : null;
    const userName = data?.username || "Attendee";
    const variant = data?.variant || "dark";

    // Format dimensions
    const dimensions = {
      og: { width: 1200, height: 630 }, // Facebook, LinkedIn, Discord
      twitter: { width: 1200, height: 600 }, // Twitter summary_large_image
      linkedin: { width: 1200, height: 627 }, // LinkedIn optimal
      square: { width: 1200, height: 1200 }, // Instagram, WhatsApp
    };

    const { width, height } = dimensions[format as keyof typeof dimensions] || dimensions.og;

    // Colors based on variant
    const isDark = variant === "dark";
    const bgColor = isDark ? "#000000" : "#ffffff";
    const textColor = isDark ? "#ffffff" : "#000000";
    const accentColor = "#878787";

    return new ImageResponse(
      (
        <div
          style={{
            height: "100%",
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            justifyContent: "center",
            backgroundColor: bgColor,
              fontFamily: 'Geist',
              fontSize: 48,
            padding: "60px",
          }}
        >
          <div style={{
              display: 'flex',
              gap: '36px',
              alignItems: 'center'
          }}>
            <span style={{ fontSize: 96, color: '#3b82f6' }}>⚕</span>
              <div style={{
                  display: 'flex',
                  flexDirection: 'column',
              }}>
                <span style={{
                    color: textColor,
                    textTransform: 'uppercase',
                    lineHeight: '56px',
                }}>{EVENT_CITY}</span>
                <span style={{
                    color: accentColor,
                    textTransform: 'uppercase',
                    lineHeight: '56px'
                }}>{EVENT_DATE}</span>
              </div>
          </div>
            <div style={{
                display: 'flex',
                gap: '36px',
                marginBottom: '32px'
            }}>
                <span style={{
                    color: textColor,
                    fontSize: '130px',
                    lineHeight: '122px',
                }}>
                    {TITLE}
                </span>
            </div>
            <div style={{
                display: 'flex',
                gap: '36px',
            }}>
                <span style={{
                    color: accentColor,
                    lineHeight: '56px',
                    textTransform: 'uppercase'
                }}>
                    {userName}
                </span>
            </div>
        </div>
      ),
      {
        width,
        height,
          fonts: [
              {
                  name: 'Geist',
                  data: await loadGoogleFont('Geist', TITLE),
                  style: 'normal',
              },{
                  name: 'Geist',
                  data: await loadGoogleFont('Geist', userName),
                  style: 'normal',
              },
          ],
      }
    );
  } catch (e) {
    console.log(`OG Image Generation Error: ${e}`);
    return new Response(`Failed to generate the image`, {
      status: 500,
    });
  }
}
