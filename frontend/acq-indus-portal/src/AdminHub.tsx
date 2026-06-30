import { useEffect, useState } from "react";

export default function AdminHub() {
  // Simulation du rôle de l'utilisateur connecté ('admin' ou 'user')
  const [userRole, setUserRole] = useState("admin");

  // Redirection vers l'application de supervision si l'utilisateur est un opérateur (user)
  useEffect(() => {
    if (userRole === "user") {
      window.location.href = "http://localhost:8080";
    }
  }, [userRole]);

  // Configuration des services/vignettes pour le profil Administrateur
  const services = [
    {
      title: "Application Supervision",
      description:
        "Interface de suivi temps réel destinée aux opérateurs. Inclut la cartographie simplifiée, le statut des ventilateurs et les alertes de l'IA.",
      url: "http://localhost:8081", // Port configuré dans docker-compose
      isInternal: false,
      color: "from-blue-500 to-indigo-600",
      icon: (
        <svg
          className="w-6 h-6 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          ></path>
        </svg>
      ),
    },
    {
      title: "Grafana Analytics",
      description:
        "Supervision technique approfondie. Permet de requêter directement InfluxDB, d'analyser les patterns temporels, de générer des alarmes et d'évaluer la précision des modèles de l'IA.",
      url: "http://localhost:3001", // Port configuré dans docker-compose
      isInternal: false,
      color: "from-amber-500 to-orange-600",
      icon: (
        <svg
          className="w-6 h-6 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M7 12l3-3 3 3 4-4M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"
          ></path>
        </svg>
      ),
    },
    {
      title: "Influxdb Data Explorer",
      description:
        "Base de données temporelle utilisée pour stocker les mesures des capteurs. Permet d'explorer les données brutes, de vérifier les écritures et d'optimiser les requêtes pour Grafana.",
      url: "http://localhost:8086", // Port configuré dans docker-compose
      isInternal: false,
      color: "from-emerald-500 to-teal-600",
      icon: (
        <svg
          className="w-6 h-6 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
          ></path>
        </svg>
      ),
    },
  ];

  // SCÉNARIO UTILISATEUR : écran de transition pendant la redirection
  if (userRole === "user") {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-900 text-slate-100">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-500 mb-4"></div>
        <p className="text-slate-400 text-sm tracking-wide">
          Chargement de votre espace de travail...
        </p>
      </div>
    );
  }

  // SCÉNARIO ADMINISTRATEUR : Affichage du Portail d'administration complet
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8 md:p-12">
      {/* Header du Hub */}
      <header className="container mx-auto mb-12 flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-800 pb-6 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 text-xs font-semibold bg-red-500/10 text-red-400 rounded-full border border-red-500/20">
              Console d'Administration
            </span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mt-2">
            ACQ-INDUS Hypervisor
          </h1>
          <p className="text-slate-400 mt-1 text-sm md:text-base">
            Portail d'accès centralisé aux infrastructures IoT et de
            supervision.
          </p>
        </div>

        {/* Simulateur de bascule de rôle pour votre phase de dev */}
        <div className="bg-slate-800 p-1.5 rounded-lg inline-flex items-center self-start md:self-auto">
          <button
            onClick={() => setUserRole("admin")}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${userRole === "admin" ? "bg-indigo-600 text-white shadow" : "text-slate-400 hover:text-white"}`}
          >
            Vue Admin
          </button>
          <button
            onClick={() => setUserRole("user")}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${userRole === "user" ? "bg-indigo-600 text-white shadow" : "text-slate-400 hover:text-white"}`}
          >
            Vue Opérateur
          </button>
        </div>
      </header>

      {/* Grille des vignettes (Cards) */}
      <main className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {services.map((service, index) => (
            <div
              key={index}
              className="group relative bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 flex flex-col justify-between hover:border-slate-600 transition-all duration-300 hover:-translate-y-1 shadow-xl hover:shadow-2xl hover:bg-slate-800"
            >
              <div>
                {/* Icône avec dégradé dynamique */}
                <div
                  className={`w-12 h-12 rounded-xl bg-gradient-to-br ${service.color} flex items-center justify-center shadow-lg mb-6 group-hover:scale-110 transition-transform duration-300`}
                >
                  {service.icon}
                </div>

                {/* Titre & Description */}
                <h3 className="text-xl font-bold text-white mb-2 tracking-tight">
                  {service.title}
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed mb-6">
                  {service.description}
                </p>
              </div>

              {/* Bouton d'action */}
              <div className="pt-4 border-t border-slate-700/50">
                <a
                  href={service.url}
                  target={service.isInternal ? "_self" : "_blank"}
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-white bg-slate-700 group-hover:bg-indigo-600 w-full justify-center py-2.5 px-4 rounded-xl transition-all duration-300 shadow-sm"
                >
                  <span>Accéder à l'application</span>
                  <svg
                    className="w-4 h-4 transform group-hover:translate-x-1 transition-transform"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M14 5l7 7m0 0l-7 7m7-7H3"
                    ></path>
                  </svg>
                </a>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Footer technique */}
      <footer className="container mx-auto mt-16 pt-6 border-t border-slate-800/60 text-center md:text-left text-xs text-slate-500">
        <p>© 2026 BG Soft - Architecture IoT Micro-services Connectée.</p>
      </footer>
    </div>
  );
}
