window.Chains = window.Chains || {};
window.Chains.View = window.Chains.View || {};

window.Chains.View.Devices = function(app) {

    var self = this;

    self.groupBy = ko.observable('type');

    self.groupByOptions = ko.observableArray(['none','type','location']);

    self.Group = function(data) {

        var self = this;

        self.id = ko.observable(data.id);
        self.devices = ko.observableArray(data.devices);

        self.name = ko.computed(function(){
            var groupBy = app.views.devices.groupBy();
            switch (self.id()) {
                case 'none':
                    return groupBy == 'none' ? 'All devices' : '(Unknown ' + groupBy + ')';
                default:
                    return self.id();
            }
        });

    };

    self.Device = function(data) {
        var self = this;

        self.callAction = function(actionName, event) {
            var url = '/services/' + data.serviceId + '/' + actionName;
            app.backend.post(url, [data.device]);
        };

        self.serviceId = ko.observable(data.serviceId);
        self.device    = ko.observable(data.device);
        self.name      = ko.observable(data.name);
        self._type     = ko.observable(data.type);
        self._location = ko.observable(data.location);
        self._data     = ko.observable(data.data);
        self.actions   = ko.observable(data.actions);

        self.cssClass = ko.computed(function(){
            return 'device device-type-' + (self._type() || 'generic');
        });

        self.data = ko.computed(function(){
			var result = [];
			var data = self._data() || {};
			for (var key in data) {
				result[result.length] = { key: key, data: data[key] };
			}
			return result;
        });

		self.location = ko.computed(function(){
			return self._location() || 'unknown';
		});

		self.type = ko.computed(function(){
			return self._type() || 'unknown';
		});

        self.icon = ko.computed(function(){
			return '/images/type-icon/' + self.type() + '.svg';
        });
    };

    self.data = ko.computed(function() {
        var result = {};
        var data = app.state.data();
        var groupBy = self.groupBy();
        for(var i=0; i < data.length; i++) {
            var service = data[i];
            var devices = service.devices();
            for(var j=0; j<devices.length; j++) {
                var device = devices[j];
                if (device.id() == '_service')
                    continue;
                var dev = {
                    serviceId: service.id(),
                    device:    device.id(),
                    name:      device.id(),
                    location:  null,
                    type:      null,
					data:      {},
                    actions: []
                };
                var deviceData = device.data();

                for (var prop in deviceData.data) {
                    if (deviceData.data[prop].actions) {
                        dev.actions = dev.actions.concat(deviceData.data[prop].actions);
                    }
                }

                for(var key in deviceData) {
                    dev[key] = deviceData[key];
                }
                var group = groupBy == 'none' ? 'none' : dev[groupBy];
                if (group === null || group === undefined) group = 'none';
                if (!result[group])
                    result[group] = [];
                result[group][ result[group].length ] = new self.Device(dev);

            }
        }

        var result2 = [];
        for(var groupId in result) {
            if (groupId == 'none')
                continue;
            var group = new self.Group({
                id: groupId,
                devices: result[groupId]
            });
            result2[result2.length] = group;
        }

        if (result.none) {
            var groupId = 'none';
            var group = new self.Group({
                id: groupId,
                devices: result[groupId]
            });
            result2[result2.length] = group;
        }

        return result2;
    });
};
