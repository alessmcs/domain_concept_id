Project Overview
You will create the FlexiBook application for micro-enterprises (i.e., one-person businesses such
as hairdressers or physiotherapists) that first allows various services and service combos to be
specified and then supports the owner of the business in the appointment booking process.
Business Setup
The FlexiBook application has a built-in user account for the business owner called owner.
Initially, the password for this account is set to owner, but this can be changed later on. Only the
owner may set up the business, i.e., provide general information about the business and its services.
After logging in, the owner first specifies the name of the business, its address, phone number, and
email address as well as its weekly business hours including lunch breaks, holidays, and vacation.
Then, the owner enters a list of services. Each service has a name and a duration (i.e., how long it
takes to provide this service). For a hairdresser, for example, services may be wash, extensions,
color, highlights, cut, and blow dry. A service is often combined with other services into a
sequential series of services called a service combo. Some services may require another service
(e.g., after applying a color, the hair needs to be washed). Other services may be combined
optionally in a specific order (e.g., one may get a cut and optionally a wash and optionally a blow
dry, but the wash has to be done before the cut and the blow dry after the cut). In a service combo,
there is always a main service which is mandatory and determines the name of the service combo
(e.g., in the wash/cut/blow dry combo, cut is the main service). A service may be the main service
for several service combos (e.g., “Cut - Regular” and “Cut - Deluxe”). Furthermore, some services
include a downtime, during which the owner may provide another service (e.g., a color
appointment takes 1 ¼ hours in total, which includes 45min for the application of the color and
30min of waiting time to let the color set; during these 30min the owner is free to work on another
customer). The owner may update a service or service combo after a warning that all future
appointments of the service or service combo will be affected. The owner may cancel the update
of a service or service combo, if she does not want to change these appointments. The owner may
delete a service or service combo, only if no future appointments exist for the service or service
combo.
Appointment Booking Process
For a customer to book an appointment, the customer first has to sign up for an account. Each
account has a unique username and a password. A customer may change the username and
password at any time. A customer may also delete her account, which will delete all appointments
of the customer after a warning. A customer may cancel the deletion of her account, if she does
not want to delete all appointments. To book an appointment, the customer first logs in. The
customer then views the appointment calendar. At this point, the customer either selects (i) the
desired service and an available time slot or (ii) the desired service combo (i.e., the mandatory
main service and any optional services) and an available time slot. The customer may update or
cancel her appointment up until the day before the appointment date.