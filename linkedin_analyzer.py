import pandas as pd
import numpy as np


class LinkedInAnalyzer:

    def __init__(self, dataframe):
        self.df_original = dataframe.copy()
        self.df = self._limpiar_dataframe()

    # ======================================================
    # DETECTAR AUTOMÁTICAMENTE FECHAS
    # ======================================================
    def obtener_periodo(self):

        posibles = [
            # Español
            "Fecha",
            "Fecha de publicación",
            "Fecha de creación",
            "Fecha de publicación del contenido",

            # Inglés
            "Date",
            "Published date",
            "Publication date",
            "Publish date",
            "Created date",
            "Creation date"
        ]

        columna = self.buscar_columna(posibles)

        if columna is None:
            return None

        fechas = pd.to_datetime(
            self.df[columna],
            errors="coerce",
            dayfirst=True
        ).dropna()

        if fechas.empty:
            return None

        return (
            fechas.min().strftime("%d/%m/%Y"),
            fechas.max().strftime("%d/%m/%Y")
        )

    # ======================================================
    # LIMPIEZA
    # ======================================================

    def _limpiar_dataframe(self):

        df = self.df_original.copy()

        # Eliminar columnas totalmente vacías
        df = df.dropna(axis=1, how="all")

        # Eliminar columnas completamente a cero
        columnas_validas = []

        for col in df.columns:

            serie = pd.to_numeric(df[col], errors="coerce")

            # Si es texto la dejamos
            if serie.isna().all():
                columnas_validas.append(col)
                continue

            # Si tiene algún dato distinto de 0
            if not (serie.fillna(0) == 0).all():
                columnas_validas.append(col)

        df = df[columnas_validas]

        # Quitar espacios en nombres
        df.columns = df.columns.str.strip()

        return df

    # ======================================================
    # BUSCAR COLUMNAS
    # ======================================================

    def buscar_columna(self, posibles):

        for nombre in posibles:
            if nombre in self.df.columns:
                return nombre

        return None

    # ======================================================
    # NORMALIZAR PUBLICACIONES PRINCIPALES
    # ======================================================

    def obtener_publicaciones(self):

        url_columna = self.buscar_columna([
            "URL de la publicación",
            "URL"
        ])

        fecha_columna = self.buscar_columna([
            "Fecha de publicación",
            "Fecha"
        ])

        interacciones_columna = self.buscar_columna([
            "Interacciones"
        ])

        impresiones_columna = self.buscar_columna([
            "Impresiones",
            "Impressions"
        ])

        if url_columna is None:
            return []

        publicaciones = []

        for _, fila in self.df.iterrows():

            url = fila[url_columna]

            # Ignorar filas sin URL
            if pd.isna(url) or str(url).strip() == "":
                continue

            publicacion = {
                "URL": str(url).strip()
            }

            # ----------------------------------------------
            # FECHA
            # ----------------------------------------------

            if fecha_columna:

                fecha = pd.to_datetime(
                    fila[fecha_columna],
                    errors="coerce",
                    dayfirst=True
                )

                if pd.notna(fecha):
                    publicacion["Fecha"] = fecha.strftime(
                        "%d/%m/%Y"
                    )

            # ----------------------------------------------
            # INTERACCIONES
            # ----------------------------------------------

            if interacciones_columna:

                interacciones = pd.to_numeric(
                    fila[interacciones_columna],
                    errors="coerce"
                )

                if pd.notna(interacciones):
                    publicacion["Interacciones"] = int(
                        interacciones
                    )

            # ----------------------------------------------
            # IMPRESIONES
            # ----------------------------------------------

            if impresiones_columna:

                impresiones = pd.to_numeric(
                    fila[impresiones_columna],
                    errors="coerce"
                )

                if pd.notna(impresiones):
                    publicacion["Impresiones"] = int(
                        impresiones
                    )

            publicaciones.append(publicacion)

        print("PUBLICACIONES NORMALIZADAS:", len(publicaciones))

        return publicaciones

    # ======================================================
    # PUBLICACIONES DESTACADAS
    # ======================================================

    def publicaciones_destacadas(self):

        publicaciones = self.obtener_publicaciones()

        if not publicaciones:
            return {
                "Top 5": [],
                "Bottom 5": []
            }

        publicaciones_validas = [
            p for p in publicaciones
            if "Impresiones" in p
        ]

        # --------------------------------------------------
        # CALCULAR ENGAGEMENT
        # --------------------------------------------------

        for publicacion in publicaciones_validas:

            impresiones = publicacion.get("Impresiones", 0)
            interacciones = publicacion.get("Interacciones", 0)

            if impresiones > 0:

                engagement = (
                    interacciones / impresiones
                ) * 100

                publicacion["Engagement"] = round(
                    engagement,
                    2
                )

            else:

                publicacion["Engagement"] = 0.0

        # --------------------------------------------------
        # ORDENAR POR IMPRESIONES
        # --------------------------------------------------

        top_5 = sorted(
            publicaciones_validas,
            key=lambda p: p["Impresiones"],
            reverse=True
        )[:5]

        bottom_5 = sorted(
            publicaciones_validas,
            key=lambda p: p["Impresiones"]
        )[:5]

        return {
            "Top 5": top_5,
            "Bottom 5": bottom_5
        }

    # ======================================================
    # MÉTRICAS
    # ======================================================

    def metricas(self):

        impresiones = self.buscar_columna([
            "Impresiones",
            "Impressions"
        ])

        reacciones = self.buscar_columna([
            "Reacciones",
            "Reactions"
        ])

        comentarios = self.buscar_columna([
            "Comentarios",
            "Comments"
        ])

        compartidos = self.buscar_columna([
            "Compartidos",
            "Shares"
        ])

        estadisticas = {}

        # --------------------------------------------------
        # PUBLICACIONES
        # --------------------------------------------------

        estadisticas["Publicaciones"] = len(self.df)

        # --------------------------------------------------
        # IMPRESIONES
        # --------------------------------------------------

        if impresiones:

            serie_impresiones = pd.to_numeric(
                self.df[impresiones],
                errors="coerce"
            ).dropna()

            if not serie_impresiones.empty:

                estadisticas["Impresiones totales"] = int(
                    serie_impresiones.sum()
                )

                estadisticas["Impresiones medias"] = round(
                    serie_impresiones.mean(),
                    1
                )

                estadisticas["Mediana de impresiones"] = round(
                    serie_impresiones.median(),
                    1
                )

                estadisticas["Mínimo impresiones"] = int(
                    serie_impresiones.min()
                )

                estadisticas["Máximo impresiones"] = int(
                    serie_impresiones.max()
                )

                estadisticas["Desviación estándar impresiones"] = round(
                    serie_impresiones.std(),
                    1
                )

                estadisticas["Publicaciones por encima de la media"] = int(
                    (serie_impresiones > serie_impresiones.mean()).sum()
                )

                estadisticas["Publicaciones por debajo de la media"] = int(
                    (serie_impresiones < serie_impresiones.mean()).sum()
                )

        # --------------------------------------------------
        # FRECUENCIA DE PUBLICACIÓN
        # --------------------------------------------------

        posibles_fechas = [
            "Fecha",
            "Fecha de publicación",
            "Fecha de creación",
            "Fecha de publicación del contenido",
            "Date",
            "Published date",
            "Publication date",
            "Publish date",
            "Created date",
            "Creation date"
        ]

        columna_fecha = self.buscar_columna(posibles_fechas)

        if columna_fecha:

            fechas = pd.to_datetime(
                self.df[columna_fecha],
                errors="coerce",
                dayfirst=True
            ).dropna().sort_values()

            if not fechas.empty:

                fecha_inicio = fechas.min()
                fecha_fin = fechas.max()

                dias_periodo = (
                    fecha_fin - fecha_inicio
                ).days

                # Evitamos divisiones por cero si todas
                # las publicaciones tienen la misma fecha.
                dias_calculo = max(1, dias_periodo)

                semanas_periodo = max(
                    1,
                    dias_calculo / 7
                )

                meses_periodo = max(
                    1,
                    dias_calculo / 30.44
                )

                estadisticas["Días del periodo analizado"] = int(
                    dias_periodo
                )

                estadisticas["Semanas del periodo analizado"] = round(
                    semanas_periodo,
                    1
                )

                estadisticas["Meses del periodo analizado"] = round(
                    meses_periodo,
                    1
                )

                estadisticas["Publicaciones por semana"] = round(
                    len(fechas) / semanas_periodo,
                    2
                )

                estadisticas["Publicaciones por mes"] = round(
                    len(fechas) / meses_periodo,
                    2
                )

                # --------------------------------------------------
                # INTERVALO MEDIO ENTRE PUBLICACIONES
                # --------------------------------------------------

                if len(fechas) > 1:

                    diferencias = fechas.diff().dropna()

                    intervalo_medio = (
                        diferencias.dt.total_seconds().mean()
                        / 86400
                    )

                    estadisticas[
                        "Intervalo medio entre publicaciones (días)"
                    ] = round(
                        intervalo_medio,
                        2
                    )

        # --------------------------------------------------
        # REACCIONES
        # --------------------------------------------------

        if reacciones:

            serie = pd.to_numeric(
                self.df[reacciones],
                errors="coerce"
            ).fillna(0)

            estadisticas["Reacciones totales"] = int(
                serie.sum()
            )

            # --------------------------------------------------
            # ENGAGEMENT GLOBAL
            # --------------------------------------------------

            if impresiones and reacciones:

                serie_impresiones = pd.to_numeric(
                    self.df[impresiones],
                    errors="coerce"
                ).fillna(0)

                serie_reacciones = pd.to_numeric(
                    self.df[reacciones],
                    errors="coerce"
                ).fillna(0)

                impresiones_totales = serie_impresiones.sum()
                reacciones_totales = serie_reacciones.sum()

                if impresiones_totales > 0:

                    engagement_global = (
                        reacciones_totales
                        / impresiones_totales
                    ) * 100

                    estadisticas["Engagement global (%)"] = round(
                        engagement_global,
                        2
                    )

        # --------------------------------------------------
        # COMENTARIOS
        # --------------------------------------------------

        if comentarios:

            serie = pd.to_numeric(
                self.df[comentarios],
                errors="coerce"
            ).fillna(0)

            estadisticas["Comentarios totales"] = int(
                serie.sum()
            )

        # --------------------------------------------------
        # COMPARTIDOS
        # --------------------------------------------------

        if compartidos:

            serie = pd.to_numeric(
                self.df[compartidos],
                errors="coerce"
            ).fillna(0)

            estadisticas["Compartidos totales"] = int(
                serie.sum()
            )

        return estadisticas    
    

    # ======================================================
    # RESUMEN PARA IA
    # ======================================================

    def resumen_para_ia(self):

        resumen = self.metricas()

        texto = []

        texto.append("RESUMEN DEL HISTÓRICO DE LINKEDIN")

        # --------------------------------------------------
        # PERIODO
        # --------------------------------------------------

        periodo = self.obtener_periodo()

        if periodo:
            texto.append("")
            texto.append(
                f"Periodo analizado: {periodo[0]} - {periodo[1]}"
            )

        # --------------------------------------------------
        # MÉTRICAS GENERALES
        # --------------------------------------------------

        texto.append("")

        for clave, valor in resumen.items():
            texto.append(f"{clave}: {valor}")

        # --------------------------------------------------
        # PUBLICACIONES DESTACADAS
        # --------------------------------------------------

        destacadas = self.publicaciones_destacadas()

        texto.append("")
        texto.append("PUBLICACIONES DESTACADAS")
        texto.append("")

        # --------------------------------------------------
        # TOP 5
        # --------------------------------------------------

        texto.append("TOP 5 PUBLICACIONES POR IMPRESIONES")

        for posicion, publicacion in enumerate(
            destacadas["Top 5"],
            start=1
        ):

            texto.append(
                f"{posicion}. "
                f"Fecha: {publicacion.get('Fecha', 'N/D')} | "
                f"Impresiones: {publicacion.get('Impresiones', 0)} | "
                f"Interacciones: {publicacion.get('Interacciones', 0)} | "
                f"Engagement: {publicacion.get('Engagement', 0)}% | "
                f"URL: {publicacion.get('URL', 'N/D')}"
            )

        # --------------------------------------------------
        # BOTTOM 5
        # --------------------------------------------------

        texto.append("")
        texto.append("BOTTOM 5 PUBLICACIONES POR IMPRESIONES")

        for posicion, publicacion in enumerate(
            destacadas["Bottom 5"],
            start=1
        ):

            texto.append(
                f"{posicion}. "
                f"Fecha: {publicacion.get('Fecha', 'N/D')} | "
                f"Impresiones: {publicacion.get('Impresiones', 0)} | "
                f"Interacciones: {publicacion.get('Interacciones', 0)} | "
                f"Engagement: {publicacion.get('Engagement', 0)}% | "
                f"URL: {publicacion.get('URL', 'N/D')}"
            )

        return "\n".join(texto)
