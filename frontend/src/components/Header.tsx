export default function Header() {
  return (
    <header className="site-header">
      <a className="wordmark" href="#" aria-label="AutoValeur, accueil">
        auto<span aria-hidden="true">/</span>valeur
      </a>
      <span className="header-locality">Maroc <span aria-hidden="true">/</span> MAD</span>
    </header>
  );
}
