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
            errors="coerce"
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

        estadisticas["Publicaciones"] = len(self.df)

        if impresiones:

            serie = pd.to_numeric(
                self.df[impresiones],
                errors="coerce"
            ).fillna(0)

            estadisticas["Impresiones totales"] = int(serie.sum())
            estadisticas["Impresiones medias"] = round(serie.mean(), 1)
            estadisticas["Máximo impresiones"] = int(serie.max())

        if reacciones:

            serie = pd.to_numeric(
                self.df[reacciones],
                errors="coerce"
            ).fillna(0)

            estadisticas["Reacciones"] = int(serie.sum())

        if comentarios:

            serie = pd.to_numeric(
                self.df[comentarios],
                errors="coerce"
            ).fillna(0)

            estadisticas["Comentarios"] = int(serie.sum())

        if compartidos:

            serie = pd.to_numeric(
                self.df[compartidos],
                errors="coerce"
            ).fillna(0)

            estadisticas["Compartidos"] = int(serie.sum())

        return estadisticas

    # ======================================================
    # RESUMEN IA
    # ======================================================

    def resumen_para_ia(self):

        resumen = self.metricas()

        texto = []

        texto.append("RESUMEN DEL HISTÓRICO DE LINKEDIN")
        periodo = self.obtener_periodo()

        if periodo:
            texto.append("")
            texto.append(
                f"Periodo analizado: {periodo[0]} - {periodo[1]}"
            )
        texto.append("")

        for clave, valor in resumen.items():

            texto.append(f"{clave}: {valor}")


        return "\n".join(texto)