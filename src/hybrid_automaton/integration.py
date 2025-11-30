class IntegrationMethods: 
    def default_integration(self, x, aux_x, ctx, xdot):
        return x + xdot * ctx['dt']