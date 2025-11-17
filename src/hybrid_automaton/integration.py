class IntegrationMethods: 
    def default_integration(self, x, aux_x, xdot, dt):
        return x + xdot * dt