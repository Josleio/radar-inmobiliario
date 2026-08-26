from typing import Optional

from pydantic import BaseModel, Field, field_validator


class InmuebleSilver(BaseModel):
    """
    Contrato de datos estricto para la capa Silver.
    Cualquier dato que no cumpla con esto será rechazado o casteado.
    """
    id_inmueble: str = Field(..., description="ID único combinado con la fuente")
    fuente: str
    barrio: str
    precio_cop: int = Field(gt=0, description="El precio debe ser estrictamente positivo")
    area_m2: int = Field(gt=0, description="El área debe ser mayor a 0")
    habitaciones: int = Field(ge=0, description="No puede ser negativo")
    banos: int = Field(ge=0, description="No puede ser negativo")
    precio_x_m2: Optional[float] = None

    @field_validator('barrio', mode='before')
    def clean_barrio(cls, v):
        """Si no hay barrio o viene raro, lo estandariza."""
        if not v or str(v).strip() == "":
            return "Sin Barrio"
        # Convierte " el POBLADO " en "El Poblado"
        return str(v).strip().title()

    @field_validator('precio_x_m2', mode='before')
    def calculate_precio_m2(cls, v, info):
        """Autocalcula el precio si viene nulo."""
        if v is not None:
            return round(float(v), 2)
        
        # Accedemos a los datos previamente validados
        if 'precio_cop' in info.data and 'area_m2' in info.data:
            precio = info.data['precio_cop']
            area = info.data['area_m2']
            if area > 0:
                return round(precio / area, 2)
        return None