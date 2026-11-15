export function LandingFooter() {
  return (
    <footer className="landing-footer">
      <div className="landing-footer-inner">
        <div className="landing-footer-brands">
          <a href="#top" className="landing-footer-project" aria-label="MODVIIRS, back to the top">
            <img src="/icon.png" alt="" width="40" height="40" loading="lazy" decoding="async" />
            <span>MODVIIRS</span>
          </a>
          <div className="landing-footer-team">
            <img src="/images/astra11-cropped.png" alt="Astra 11 team" width="1536" height="1024" loading="lazy" decoding="async" />
          </div>
          <a href="https://www.nasa.gov/" className="landing-footer-nasa" aria-label="NASA, official website">
            <img src="/images/nasa-transparent.png" alt="NASA" width="1385" height="1136" loading="lazy" decoding="async" />
          </a>
        </div>
      </div>
    </footer>
  )
}
