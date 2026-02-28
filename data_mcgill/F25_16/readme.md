Project Description
You will create the CheESCEManager application for a facility that ages Comté cheese. CheESCEManager is
intended to be used by a facility manager to effectively manage the aging process of cheese. Upon instruction of
the facility manager, a robot takes care of the regular washing and turning of cheese wheels. The cheese wheels are
supplied by local farmers that cannot age the cheese by themselves. Farmers use the application to individually
track the details of their cheese wheels. Once matured, cheese wheels are sold to wholesale companies.
The application has a built-in user account for the facility manager called manager@cheesce.fr. Initially, the
password for this account is set to manager, but this can be changed later by the person with manager access.
When a farmer registers in the system, they provide an email address as the account name and a password as well
as a postal address and an optional name. The account name and password identify each farmer. Once entered, the
email address of a farmer cannot be changed. However, the facility manager can delete a farmer from the
application, but only if the farmer has not yet supplied any cheese to the facility.
The facility manager configures the shelves of the facility. Shelves are always arranged in a parallel fashion with an
aisle separating two shelves that is big enough for the robot. A shelf is identified by an ID, which consists of a letter
and two numbers. A shelf has a (potentially) unlimited number of columns and up to ten rows. The first column the
robot encounters when moving along an aisle is referred to as column 1, with each subsequent column being
numbered one higher than the previous one. Similarly, the bottom row is referred to as row 1, while the top row is
referred to as at the most 10. A row of a column of a shelf fits exactly one cheese wheel. It is not possible to update
the shelf configuration, but the facility manager may delete a whole shelf if there is no cheese stored on the shelf.
The facility manager purchases a number of fresh cheese wheels from a farmer. While the purchase date is tracked
by the application, the price of the purchase is out of scope for the application. At the time of the purchase, it is
decided for how many months the cheese wheels are being aged (i.e., six, twelve, twenty four, or thirty six months).
This can later be changed but it is only possible to increase the number of months. When the cheese wheels arrive
at the facility (which happens on the purchase date), each is assigned to its shelf (i.e., to a specific column and row
of a shelf). It may be necessary to move a cheese wheel to a different location on the same shelf or to a different
shelf altogether at some point during the aging process. In rare cases, it may happen that one of the cheese wheels
goes bad, in which case the cheese wheel is marked as spoiled and removed from its shelf.
Similarly, the facility manager fulfils an order of a number of aged cheese wheels from a wholesale company. An
order may only be for one kind of cheese (e.g., only six months or only twelve months but not both). Again, the
price of the order is out of scope for the application, but the order date is tracked by the application. Furthermore,
the delivery date is decided at the time of the order. For example, a cheese wheel which was purchased on March
1st to be aged for six months can be ordered at any date on or after March 1st but can only be delivered on or after
September 1st (i.e., its maturation date). The application assigns available cheese wheels to the order accordingly,
and if there are not enough cheese wheels available, the application tracks how many cheese wheels are missing
for the order. This number may have to be updated when a cheese wheel goes bad. At the delivery date, the cheese
wheels are shipped to the wholesale company’s address, but this is out of scope for the application.
For an order to be made, the wholesale company’s name and address must be entered by the facility manager, who
can also update this information. The facility manager may also delete a wholeseller but only if no cheese has been
ordered by the wholeseller.
Several reports are available to the facility manager: (i) a list of all farmers and, for a farmer, the cheese wheels that
have been supplied by the farmer and when as well as the months each cheese wheel is to be aged and whether it
is spoiled; (ii) a list of all shelves and, for a shelf, the cheese wheels that are stored on the shelf and where as well as
the months each cheese wheel is to be aged; (iii) a list of all wholesale companies and, for a wholesale company,
the cheese wheels that have been ordered by them at what date and for what delivery date as well as the months
the cheese is to be aged. The first report is also available to a farmer.
More details of the robot behavior will be provided for a later deliverable. For now, it is sufficient to know that
there is only one robot in the facility. To support the facility’s operations, the robot knows (a) its current location
relative to a shelf as well as relative to a particular cheese wheel and (b) whether it is facing the direction of an
aisle. Last but not least, the robot logs all its actions.